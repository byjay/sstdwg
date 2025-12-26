// SSTDMS Mobile App - Service Worker
// Seastar Design - World Shipbuilding & Offshore Design Provider

const CACHE_NAME = 'sstdms-mobile-v1.0.0';
const STATIC_CACHE_NAME = 'sstdms-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'sstdms-dynamic-v1.0.0';

// 캐시할 정적 파일들
const STATIC_FILES = [
  '/',
  '/src/index.html',
  '/styles/mobile.css',
  '/styles/components.css',
  '/js/app.js',
  '/js/auth.js',
  '/js/api.js',
  '/js/notifications.js',
  '/js/offline.js',
  '/js/touch-handler.js',
  '/manifest.json',
  // 폰트
  'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap',
  // 아이콘들 (실제 파일이 있을 때 추가)
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// 동적으로 캐시할 API 엔드포인트
const DYNAMIC_CACHE_URLS = [
  '/api/dashboard/stats',
  '/api/projects',
  '/api/documents',
  '/api/auth/verify'
];

// 오프라인 폴백 페이지
const OFFLINE_PAGE = '/offline.html';

// 서비스 워커 설치
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker 설치 중...');
  
  event.waitUntil(
    Promise.all([
      // 정적 파일 캐시
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('📦 정적 파일 캐시 중...');
        return cache.addAll(STATIC_FILES.filter(url => !url.startsWith('http')));
      }),
      
      // 외부 리소스 개별 캐시 (CORS 문제 방지)
      caches.open(STATIC_CACHE_NAME).then(async (cache) => {
        const externalUrls = STATIC_FILES.filter(url => url.startsWith('http'));
        for (const url of externalUrls) {
          try {
            const response = await fetch(url, { mode: 'cors' });
            if (response.ok) {
              await cache.put(url, response);
            }
          } catch (error) {
            console.warn(`외부 리소스 캐시 실패: ${url}`, error);
          }
        }
      })
    ]).then(() => {
      console.log('✅ Service Worker 설치 완료');
      // 즉시 활성화
      return self.skipWaiting();
    })
  );
});

// 서비스 워커 활성화
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker 활성화 중...');
  
  event.waitUntil(
    Promise.all([
      // 이전 캐시 정리
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName.startsWith('sstdms-')) {
              console.log(`🗑️ 이전 캐시 삭제: ${cacheName}`);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // 모든 클라이언트 제어
      self.clients.claim()
    ]).then(() => {
      console.log('✅ Service Worker 활성화 완료');
    })
  );
});

// 네트워크 요청 가로채기
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Chrome extension 요청 무시
  if (url.protocol === 'chrome-extension:') {
    return;
  }
  
  // GET 요청만 캐시 처리
  if (request.method !== 'GET') {
    return;
  }
  
  event.respondWith(
    handleFetchRequest(request)
  );
});

async function handleFetchRequest(request) {
  const url = new URL(request.url);
  
  try {
    // 1. 정적 파일 요청 처리
    if (isStaticFile(url.pathname)) {
      return await handleStaticRequest(request);
    }
    
    // 2. API 요청 처리
    if (url.pathname.startsWith('/api/')) {
      return await handleApiRequest(request);
    }
    
    // 3. HTML 페이지 요청 처리
    if (request.headers.get('accept')?.includes('text/html')) {
      return await handlePageRequest(request);
    }
    
    // 4. 기타 요청은 네트워크 우선
    return await fetch(request);
    
  } catch (error) {
    console.error('Fetch 처리 오류:', error);
    return await handleOfflineRequest(request);
  }
}

// 정적 파일 요청 처리 (캐시 우선)
async function handleStaticRequest(request) {
  const cache = await caches.open(STATIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    // 백그라운드에서 업데이트 확인
    updateCacheInBackground(request, cache);
    return cachedResponse;
  }
  
  // 캐시에 없으면 네트워크에서 가져와서 캐시
  const networkResponse = await fetch(request);
  if (networkResponse.ok) {
    cache.put(request, networkResponse.clone());
  }
  return networkResponse;
}

// API 요청 처리 (네트워크 우선, 캐시 폴백)
async function handleApiRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  
  try {
    // 네트워크 우선 시도
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // 성공하면 캐시 업데이트
      if (shouldCacheApiResponse(request.url)) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    }
    
    throw new Error(`HTTP ${networkResponse.status}`);
    
  } catch (error) {
    console.log('API 네트워크 요청 실패, 캐시 확인:', error.message);
    
    // 네트워크 실패 시 캐시에서 찾기
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      // 오프라인 표시를 위한 헤더 추가
      const response = cachedResponse.clone();
      response.headers.set('X-Served-From', 'cache');
      return response;
    }
    
    // 캐시에도 없으면 오프라인 응답
    return new Response(
      JSON.stringify({
        success: false,
        message: '오프라인 상태입니다',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// HTML 페이지 요청 처리
async function handlePageRequest(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      return networkResponse;
    }
    throw new Error(`HTTP ${networkResponse.status}`);
  } catch (error) {
    // 오프라인일 때 메인 페이지 반환
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cachedPage = await cache.match('/src/index.html') || 
                      await cache.match('/');
    
    if (cachedPage) {
      return cachedPage;
    }
    
    // 캐시에도 없으면 기본 오프라인 페이지
    return new Response(
      `
      <!DOCTYPE html>
      <html>
        <head>
          <title>SSTDMS - 오프라인</title>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { 
              font-family: -apple-system, BlinkMacSystemFont, sans-serif;
              display: flex; 
              align-items: center; 
              justify-content: center; 
              height: 100vh; 
              margin: 0;
              background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
              color: white;
              text-align: center;
            }
            .container { max-width: 400px; padding: 2rem; }
            h1 { font-size: 2rem; margin-bottom: 1rem; }
            p { opacity: 0.9; line-height: 1.6; }
            .retry-btn {
              background: rgba(255,255,255,0.2);
              border: 1px solid rgba(255,255,255,0.3);
              color: white;
              padding: 0.75rem 1.5rem;
              border-radius: 8px;
              cursor: pointer;
              margin-top: 1rem;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🌐 오프라인 상태</h1>
            <p>인터넷 연결을 확인하고 다시 시도해주세요.</p>
            <button class="retry-btn" onclick="window.location.reload()">
              다시 시도
            </button>
          </div>
        </body>
      </html>
      `,
      {
        headers: { 'Content-Type': 'text/html' }
      }
    );
  }
}

// 오프라인 요청 처리
async function handleOfflineRequest(request) {
  const url = new URL(request.url);
  
  // 캐시에서 찾기
  const cacheNames = [STATIC_CACHE_NAME, DYNAMIC_CACHE_NAME];
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
  }
  
  // 캐시에도 없으면 기본 오프라인 응답
  if (request.headers.get('accept')?.includes('text/html')) {
    return await handlePageRequest(request);
  }
  
  return new Response('오프라인 상태입니다', { 
    status: 503,
    statusText: 'Service Unavailable'
  });
}

// 백그라운드 캐시 업데이트
async function updateCacheInBackground(request, cache) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse);
    }
  } catch (error) {
    // 백그라운드 업데이트 실패는 무시
    console.log('백그라운드 캐시 업데이트 실패:', error.message);
  }
}

// 정적 파일 여부 확인
function isStaticFile(pathname) {
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'];
  return staticExtensions.some(ext => pathname.endsWith(ext)) ||
         pathname === '/' ||
         pathname.endsWith('.html');
}

// API 응답 캐시 여부 결정
function shouldCacheApiResponse(url) {
  const cacheableEndpoints = [
    '/api/dashboard/stats',
    '/api/projects',
    '/api/documents',
    '/api/user/profile'
  ];
  
  return cacheableEndpoints.some(endpoint => url.includes(endpoint));
}

// 푸시 알림 처리
self.addEventListener('push', (event) => {
  console.log('📱 푸시 알림 수신:', event);
  
  const options = {
    body: '새로운 알림이 있습니다',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '확인',
        icon: '/icons/checkmark.png'
      },
      {
        action: 'close',
        title: '닫기',
        icon: '/icons/xmark.png'
      }
    ]
  };
  
  if (event.data) {
    const data = event.data.json();
    options.body = data.body || options.body;
    options.title = data.title || 'SSTDMS';
  }
  
  event.waitUntil(
    self.registration.showNotification('SSTDMS', options)
  );
});

// 알림 클릭 처리
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 알림 클릭:', event);
  
  event.notification.close();
  
  if (event.action === 'close') {
    return;
  }
  
  // 앱 열기 또는 포커스
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === self.location.origin && 'focus' in client) {
          return client.focus();
        }
      }
      
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});

// 백그라운드 동기화
self.addEventListener('sync', (event) => {
  console.log('🔄 백그라운드 동기화:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// 백그라운드 동기화 실행
async function doBackgroundSync() {
  try {
    // 오프라인 중에 저장된 데이터 동기화
    const offlineData = await getOfflineData();
    
    for (const data of offlineData) {
      try {
        await fetch(data.url, {
          method: data.method,
          headers: data.headers,
          body: data.body
        });
        
        // 성공하면 오프라인 데이터에서 제거
        await removeOfflineData(data.id);
      } catch (error) {
        console.error('동기화 실패:', error);
      }
    }
    
    console.log('✅ 백그라운드 동기화 완료');
  } catch (error) {
    console.error('❌ 백그라운드 동기화 오류:', error);
  }
}

// 오프라인 데이터 관리 (IndexedDB 사용 권장, 여기서는 간단히 구현)
async function getOfflineData() {
  // 실제 구현에서는 IndexedDB 사용
  return [];
}

async function removeOfflineData(id) {
  // 실제 구현에서는 IndexedDB에서 제거
  console.log(`오프라인 데이터 제거: ${id}`);
}

// 메시지 처리 (클라이언트와 통신)
self.addEventListener('message', (event) => {
  console.log('💬 클라이언트 메시지:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

console.log('🎯 SSTDMS Service Worker 로드 완료');

