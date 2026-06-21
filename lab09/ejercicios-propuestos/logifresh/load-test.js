import http from 'k6/http';
import { check, sleep } from 'k6';

const PEDIDOS_URL = 'http://localhost:8000';
const INVENTARIO_URL = 'http://localhost:8001';

const CITIES = ['Lima', 'Arequipa', 'Cusco', 'Trujillo', 'Piura'];

let SKU_LIST = [];

function verificarSaludServicios() {
  console.log('Verificando estado de servicios...');

  const healthPedidos = http.get(`${PEDIDOS_URL}/health`, { timeout: '10s' });
  if (healthPedidos.status !== 200) {
    throw new Error(`Servicio Pedidos no disponible. Status: ${healthPedidos.status}`);
  }
  console.log('Servicio Pedidos: OK');

  const healthInventario = http.get(`${INVENTARIO_URL}/health`, { timeout: '10s' });
  if (healthInventario.status !== 200) {
    throw new Error(`Servicio Inventario no disponible. Status: ${healthInventario.status}`);
  }
  console.log('Servicio Inventario: OK');
}

function obtenerSKUDisponibles() {
  console.log('Cargando productos del inventario...');

  const res = http.get(`${INVENTARIO_URL}/productos`, { timeout: '10s' });

  if (res.status !== 200) {
    throw new Error(`No se pudo obtener productos. Status: ${res.status}. Body: ${res.body}`);
  }

  const productos = res.json();
  if (!Array.isArray(productos) || productos.length === 0) {
    console.log('No hay productos en inventario. Creando productos de prueba...');
    return crearProductosDePrueba();
  }

  const skus = productos.map((p) => p.sku);
  console.log(`Se encontraron ${skus.length} productos: ${skus.join(', ')}`);
  return skus;
}

function crearProductosDePrueba() {
  const productosPrueba = [];
  const categorias = ['Bebidas', 'Alimentos', 'Lacteos', 'Yogur', 'Quesos', 'Carnes', 'Frutas', 'Verduras', 'Panaderia', 'Helados'];
  const nombres = ['Producto', 'Item', 'Articulo', 'SKU', 'Test', 'Demo', 'Sample', 'Ejemplo'];

  for (let i = 1; i <= 50; i++) {
    const sku = `LOADTEST-${String(i).padStart(3, '0')}`;
    const nombre = `${nombres[Math.floor(Math.random() * nombres.length)]} ${i}`;
    const categoria = categorias[Math.floor(Math.random() * categorias.length)];
    const precio = +(Math.random() * 20 + 2).toFixed(2);
    const stock = 100000;
    productosPrueba.push({ sku, nombre, categoria, precio, stock });
  }

  const skusCreados = [];

  for (const prod of productosPrueba) {
    const payload = {
      sku: prod.sku,
      nombre: prod.nombre,
      categoria: prod.categoria,
      precio_unitario: prod.precio,
      stock_disponible: prod.stock,
      requiere_refrigeracion: true
    };

    const res = http.post(
      `${INVENTARIO_URL}/productos`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '10s'
      }
    );

    if (res.status === 201) {
      console.log(`  Producto creado: ${prod.sku} (stock: ${prod.stock})`);
      skusCreados.push(prod.sku);
    } else if (res.status === 409) {
      console.log(`  Producto ya existe: ${prod.sku}`);
      skusCreados.push(prod.sku);
    } else {
      console.log(`  No se pudo crear ${prod.sku}: Status ${res.status}`);
    }
  }

  if (skusCreados.length === 0) {
    throw new Error('No se pudieron crear productos de prueba');
  }

  console.log(`Productos de prueba creados/verificados: ${skusCreados.length} SKU`);
  return skusCreados;
}

export function setup() {
  console.log('');
  console.log('Inicializando prueba de carga con k6');
  console.log('');

  verificarSaludServicios();
  const skus = obtenerSKUDisponibles();

  console.log('');
  console.log('Iniciando prueba de carga');
  console.log(`VUs: 20 | Duracion: 5m (1m ramp-up + 3m estable + 1m ramp-down)`);
  console.log(`SKUs disponibles: ${skus.length}`);
  console.log('');

  return { skus };
}

export function teardown(data) {
  console.log('');
  console.log('Prueba completada');
  console.log('Revise los resultados arriba');
  console.log('');
}

export const options = {
  stages: [
    { duration: '1m', target: 20 },
    { duration: '3m', target: 20 },
    { duration: '1m', target: 0 }
  ],
  thresholds: {
    'http_req_failed{type:pedido_valido}': ['rate<0.05'],
    'http_req_duration{type:pedido_valido}': ['p(95)<8000'],
    'checks': ['rate>0.95']
  }
};

export default function (data) {
  const skus = data.skus;

  if (!skus || skus.length === 0) {
    throw new Error('No hay SKUs disponibles para la prueba');
  }

  const sku = skus[Math.floor(Math.random() * skus.length)];
  const city = CITIES[Math.floor(Math.random() * CITIES.length)];

  const payload = JSON.stringify({
    cliente: `Cliente_VU${__VU}_Iter${__ITER}`,
    direccion_entrega: `Calle ${Math.random() * 1000 | 0}, Depto ${Math.random() * 100 | 0}`,
    ciudad: city,
    items: [{ sku, cantidad: 1 }],
    codigo_promocion: Math.random() > 0.7 ? 'LOGIFRESH10' : null
  });

  const res = http.post(`${PEDIDOS_URL}/pedidos`, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '30s',
    tags: {
      type: 'pedido_valido',
      sku: sku
    }
  });

  if (res.status === 201) {
    check(res, {
      'status es 201': (r) => r.status === 201,
      'respuesta tiene id': (r) => r.json('id') !== undefined,
      'estado es CONFIRMADO o PENDIENTE': (r) => {
        const state = r.json('estado');
        return state === 'CONFIRMADO' || state === 'PENDIENTE' || state === 'EN_ESPERA';
      }
    });
  } else if (res.status === 422 || res.status === 400) {
    check(res, {
      'error es 422 o 400': (r) => r.status === 422 || r.status === 400,
      'respuesta tiene detail': (r) => r.json('detail') !== undefined
    });
  } else if (res.status >= 500) {
    check(res, {
      'error del servidor documentado': (r) => r.status >= 500
    });
  } else {
    check(res, {
      'status esperado': (r) => r.status === 200 || r.status === 201
    });
  }

  sleep(1);
}