// SSTDMS Mobile App - 메인 애플리케이션 로직
// Seastar Design - World Shipbuilding & Offshore Design Provider

class SSTDMSMobileApp {
    constructor() {
        this.currentUser = null;
        this.currentScreen = 'login';
        this.apiBaseUrl = window.location.origin;
        this.isOnline = navigator.onLine;
        this.cache = new Map();
        
        this.init();
    }

    async init() {
        console.log('🚀 SSTDMS Mobile App 초기화 시작');
        
        // 이벤트 리스너 등록
        this.setupEventListeners();
        
        // PWA 설정
        this.setupPWA();
        
        // 오프라인 감지
        this.setupOfflineDetection();
        
        // 스플래시 화면 처리
        await this.handleSplashScreen();
        
        // 자동 로그인 확인
        await this.checkAutoLogin();
        
        console.log('✅ SSTDMS Mobile App 초기화 완료');
    }

    setupEventListeners() {
        // 메뉴 토글
        const menuToggle = document.getElementById('menu-toggle');
        const menuClose = document.getElementById('menu-close');
        const sideMenu = document.getElementById('side-menu');
        
        if (menuToggle) {
            menuToggle.addEventListener('click', () => this.toggleMenu());
        }
        
        if (menuClose) {
            menuClose.addEventListener('click', () => this.closeMenu());
        }

        // 메뉴 오버레이 생성 및 이벤트
        this.createMenuOverlay();

        // 로그인 폼
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // 비밀번호 토글
        const passwordToggle = document.getElementById('toggle-password');
        if (passwordToggle) {
            passwordToggle.addEventListener('click', () => this.togglePassword());
        }

        // 로그아웃
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // 새로고침
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshCurrentScreen());
        }

        // 알림 버튼
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => this.showNotifications());
        }

        // 메뉴 링크들
        const menuLinks = document.querySelectorAll('.menu-link');
        menuLinks.forEach(link => {
            link.addEventListener('click', (e) => this.handleMenuClick(e));
        });

        // 하단 네비게이션
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => this.handleNavClick(e));
        });

        // 터치 이벤트 최적화
        this.setupTouchEvents();
    }

    setupTouchEvents() {
        // 터치 피드백 추가
        const touchables = document.querySelectorAll('button, .touchable, .menu-link, .nav-item');
        
        touchables.forEach(element => {
            element.addEventListener('touchstart', (e) => {
                element.style.transform = 'scale(0.95)';
                element.style.opacity = '0.8';
            }, { passive: true });
            
            element.addEventListener('touchend', (e) => {
                setTimeout(() => {
                    element.style.transform = '';
                    element.style.opacity = '';
                }, 150);
            }, { passive: true });
        });

        // 스와이프 제스처
        this.setupSwipeGestures();
    }

    setupSwipeGestures() {
        let startX = 0;
        let startY = 0;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // 수평 스와이프가 수직 스와이프보다 클 때
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    // 오른쪽 스와이프 - 메뉴 열기
                    if (startX < 50) {
                        this.openMenu();
                    }
                } else {
                    // 왼쪽 스와이프 - 메뉴 닫기
                    this.closeMenu();
                }
            }
        }, { passive: true });
    }

    createMenuOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'menu-overlay';
        overlay.id = 'menu-overlay';
        overlay.addEventListener('click', () => this.closeMenu());
        document.body.appendChild(overlay);
    }

    async setupPWA() {
        // 서비스 워커 등록
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('✅ Service Worker 등록 성공:', registration);
                
                // 업데이트 확인
                registration.addEventListener('updatefound', () => {
                    console.log('🔄 새 버전 발견, 업데이트 중...');
                    this.showToast('새 버전이 있습니다. 업데이트 중...', 'info');
                });
            } catch (error) {
                console.error('❌ Service Worker 등록 실패:', error);
            }
        }

        // 앱 설치 프롬프트
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });
    }

    setupOfflineDetection() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showToast('온라인 상태로 전환되었습니다', 'success');
            this.syncOfflineData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showToast('오프라인 모드로 전환되었습니다', 'warning');
        });
    }

    async handleSplashScreen() {
        const splashScreen = document.getElementById('splash-screen');
        const app = document.getElementById('app');
        
        // 최소 2초 스플래시 화면 표시
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        if (splashScreen && app) {
            splashScreen.classList.add('hidden');
            app.style.display = 'flex';
            
            // 스플래시 화면 제거
            setTimeout(() => {
                splashScreen.remove();
            }, 500);
        }
    }

    async checkAutoLogin() {
        const savedToken = localStorage.getItem('sstdms_token');
        const rememberMe = localStorage.getItem('sstdms_remember');
        
        if (savedToken && rememberMe === 'true') {
            try {
                const response = await this.apiCall('/api/auth/verify', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${savedToken}`
                    }
                });
                
                if (response.success) {
                    this.currentUser = response.user;
                    this.showScreen('dashboard');
                    this.updateUserInfo();
                    this.showToast('자동 로그인되었습니다', 'success');
                }
            } catch (error) {
                console.error('자동 로그인 실패:', error);
                localStorage.removeItem('sstdms_token');
                localStorage.removeItem('sstdms_remember');
            }
        }
    }

    toggleMenu() {
        const sideMenu = document.getElementById('side-menu');
        const overlay = document.getElementById('menu-overlay');
        const menuToggle = document.getElementById('menu-toggle');
        
        if (sideMenu && overlay) {
            const isOpen = sideMenu.classList.contains('open');
            
            if (isOpen) {
                this.closeMenu();
            } else {
                this.openMenu();
            }
        }
    }

    openMenu() {
        const sideMenu = document.getElementById('side-menu');
        const overlay = document.getElementById('menu-overlay');
        const menuToggle = document.getElementById('menu-toggle');
        
        if (sideMenu && overlay) {
            sideMenu.classList.add('open');
            overlay.classList.add('active');
            menuToggle?.classList.add('active');
            
            // 메뉴 열릴 때 햅틱 피드백
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    }

    closeMenu() {
        const sideMenu = document.getElementById('side-menu');
        const overlay = document.getElementById('menu-overlay');
        const menuToggle = document.getElementById('menu-toggle');
        
        if (sideMenu && overlay) {
            sideMenu.classList.remove('open');
            overlay.classList.remove('active');
            menuToggle?.classList.remove('active');
        }
    }

    togglePassword() {
        const passwordInput = document.getElementById('password');
        const toggleBtn = document.getElementById('toggle-password');
        
        if (passwordInput && toggleBtn) {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            
            // 아이콘 변경
            const svg = toggleBtn.querySelector('svg');
            if (svg) {
                if (isPassword) {
                    svg.innerHTML = `
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                    `;
                } else {
                    svg.innerHTML = `
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    `;
                }
            }
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('email')?.value;
        const password = document.getElementById('password')?.value;
        const rememberMe = document.getElementById('remember-me')?.checked;
        const loginBtn = document.getElementById('login-btn');
        const errorDiv = document.getElementById('login-error');
        
        if (!email || !password) {
            this.showError('이메일과 비밀번호를 입력해주세요');
            return;
        }

        // 로딩 상태 표시
        this.setLoginLoading(true);
        
        try {
            const response = await this.apiCall('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email,
                    password,
                    remember_me: rememberMe
                })
            });
            
            if (response.success) {
                this.currentUser = response.user;
                
                // 토큰 저장
                if (response.token) {
                    localStorage.setItem('sstdms_token', response.token);
                    localStorage.setItem('sstdms_remember', rememberMe.toString());
                }
                
                // 대시보드로 이동
                this.showScreen('dashboard');
                this.updateUserInfo();
                this.loadDashboardData();
                
                this.showToast(`환영합니다, ${response.user.full_name}님!`, 'success');
                
                // 햅틱 피드백
                if (navigator.vibrate) {
                    navigator.vibrate([100, 50, 100]);
                }
            } else {
                this.showError(response.message || '로그인에 실패했습니다');
            }
        } catch (error) {
            console.error('로그인 오류:', error);
            this.showError('네트워크 오류가 발생했습니다');
        } finally {
            this.setLoginLoading(false);
        }
    }

    setLoginLoading(loading) {
        const loginBtn = document.getElementById('login-btn');
        const btnText = loginBtn?.querySelector('.btn-text');
        const btnLoader = loginBtn?.querySelector('.btn-loader');
        
        if (loginBtn) {
            loginBtn.disabled = loading;
            
            if (btnText) btnText.style.display = loading ? 'none' : 'inline';
            if (btnLoader) btnLoader.style.display = loading ? 'block' : 'none';
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            
            // 3초 후 자동 숨김
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 3000);
        }
    }

    async handleLogout() {
        try {
            await this.apiCall('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('sstdms_token')}`
                }
            });
        } catch (error) {
            console.error('로그아웃 오류:', error);
        }
        
        // 로컬 데이터 정리
        localStorage.removeItem('sstdms_token');
        localStorage.removeItem('sstdms_remember');
        this.currentUser = null;
        this.cache.clear();
        
        // 로그인 화면으로 이동
        this.showScreen('login');
        this.closeMenu();
        
        this.showToast('로그아웃되었습니다', 'info');
    }

    showScreen(screenName) {
        // 모든 화면 숨기기
        const screens = document.querySelectorAll('.screen');
        screens.forEach(screen => {
            screen.classList.remove('active');
        });
        
        // 선택된 화면 표시
        const targetScreen = document.getElementById(`${screenName}-screen`);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentScreen = screenName;
            
            // 네비게이션 상태 업데이트
            this.updateNavigation(screenName);
            
            // 화면별 데이터 로드
            this.loadScreenData(screenName);
        }
    }

    updateNavigation(screenName) {
        // 메뉴 링크 활성화
        const menuLinks = document.querySelectorAll('.menu-link');
        menuLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${screenName}`) {
                link.classList.add('active');
            }
        });
        
        // 하단 네비게이션 활성화
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.screen === screenName) {
                item.classList.add('active');
            }
        });
    }

    updateUserInfo() {
        if (!this.currentUser) return;
        
        const userInitial = document.getElementById('user-initial');
        const userName = document.getElementById('user-name');
        const userRole = document.getElementById('user-role');
        
        if (userInitial) {
            userInitial.textContent = this.currentUser.full_name.charAt(0).toUpperCase();
        }
        
        if (userName) {
            userName.textContent = this.currentUser.full_name;
        }
        
        if (userRole) {
            const roleMap = {
                'admin': '관리자',
                'registrar': '등록자',
                'user': '사용자'
            };
            userRole.textContent = roleMap[this.currentUser.category] || '사용자';
        }
        
        // 권한별 메뉴 표시/숨김
        this.updateMenuVisibility();
    }

    updateMenuVisibility() {
        const registrarMenus = document.querySelectorAll('.registrar-only');
        const adminMenus = document.querySelectorAll('.admin-only');
        
        registrarMenus.forEach(menu => {
            menu.style.display = 
                (this.currentUser.category === 'registrar' || this.currentUser.category === 'admin') 
                ? 'block' : 'none';
        });
        
        adminMenus.forEach(menu => {
            menu.style.display = 
                this.currentUser.category === 'admin' ? 'block' : 'none';
        });
    }

    handleMenuClick(e) {
        e.preventDefault();
        const link = e.currentTarget;
        const href = link.getAttribute('href');
        
        if (href && href.startsWith('#')) {
            const screenName = href.substring(1);
            this.showScreen(screenName);
            this.closeMenu();
        }
    }

    handleNavClick(e) {
        const item = e.currentTarget;
        const screenName = item.dataset.screen;
        
        if (screenName) {
            this.showScreen(screenName);
        }
    }

    async loadScreenData(screenName) {
        switch (screenName) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'projects':
                await this.loadProjectsData();
                break;
            case 'documents':
                await this.loadDocumentsData();
                break;
            // 추가 화면들...
        }
    }

    async loadDashboardData() {
        try {
            const response = await this.apiCall('/api/dashboard/stats');
            
            if (response.success) {
                this.updateDashboardStats(response.data);
                this.updateRecentActivity(response.activities);
            }
        } catch (error) {
            console.error('대시보드 데이터 로드 실패:', error);
            this.showOfflineMessage();
        }
    }

    updateDashboardStats(stats) {
        const totalProjects = document.getElementById('total-projects');
        const totalDocuments = document.getElementById('total-documents');
        const recentUploads = document.getElementById('recent-uploads');
        
        if (totalProjects) totalProjects.textContent = stats.projects || 0;
        if (totalDocuments) totalDocuments.textContent = stats.documents || 0;
        if (recentUploads) recentUploads.textContent = stats.recent_uploads || 0;
    }

    updateRecentActivity(activities) {
        const activityList = document.getElementById('activity-list');
        if (!activityList || !activities) return;
        
        if (activities.length === 0) {
            activityList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📋</div>
                    <div class="empty-title">활동 내역이 없습니다</div>
                    <div class="empty-description">새로운 활동이 있으면 여기에 표시됩니다</div>
                </div>
            `;
            return;
        }
        
        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    ${this.getActivityIcon(activity.type)}
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                </div>
                <div class="activity-time">${this.formatTime(activity.created_at)}</div>
            </div>
        `).join('');
    }

    getActivityIcon(type) {
        const icons = {
            'upload': '📤',
            'download': '📥',
            'create': '➕',
            'update': '✏️',
            'delete': '🗑️',
            'login': '🔐'
        };
        return icons[type] || '📋';
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return '방금 전';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
        return `${Math.floor(diff / 86400000)}일 전`;
    }

    async refreshCurrentScreen() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                refreshBtn.style.transform = '';
            }, 500);
        }
        
        await this.loadScreenData(this.currentScreen);
        this.showToast('새로고침 완료', 'success');
    }

    showNotifications() {
        // 알림 모달 표시 (추후 구현)
        this.showToast('알림 기능은 곧 추가될 예정입니다', 'info');
    }

    showInstallPrompt() {
        if (this.deferredPrompt) {
            this.showToast('홈 화면에 앱을 추가할 수 있습니다', 'info');
        }
    }

    async syncOfflineData() {
        // 오프라인 데이터 동기화 (추후 구현)
        console.log('오프라인 데이터 동기화 시작');
    }

    showOfflineMessage() {
        this.showToast('오프라인 상태입니다. 캐시된 데이터를 표시합니다', 'warning');
    }

    async apiCall(endpoint, options = {}) {
        // GitHub Pages 환경에서는 API 호출 대신 정적 JSON 파일 로드
        if (this.apiBaseUrl.includes('github.io')) {
            console.log(`GitHub Pages 모드: ${endpoint} -> 정적 데이터 로드`);
            
            if (endpoint === '/api/dashboard/stats') {
                return this.getMockDashboardStats();
            }
            if (endpoint === '/api/auth/login') {
                 // 데모용 가짜 로그인 처리
                const body = JSON.parse(options.body);
                return {
                    success: true,
                    user: {
                        full_name: '데모 사용자',
                        category: body.email.includes('admin') ? 'admin' : 'user'
                    },
                    token: 'demo-token'
                };
            }
            // 기타 API 호출에 대한 모의 응답
            return { success: true };
        }

        const url = `${this.apiBaseUrl}${endpoint}`;
        
        // 기본 헤더 설정
        const defaultHeaders = {
            'Content-Type': 'application/json'
        };
        
        // 인증 토큰 추가
        const token = localStorage.getItem('sstdms_token');
        if (token) {
            defaultHeaders['Authorization'] = `Bearer ${token}`;
        }
        
        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, config);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('API 호출 실패, 오프라인 모드로 전환:', error);
            // API 실패 시에도 데모 데이터 반환 (GitHub Pages 호환성)
             if (endpoint === '/api/dashboard/stats') {
                return this.getMockDashboardStats();
            }
            throw error;
        }
    }

    async getMockDashboardStats() {
        // drawings.json에서 실제 데이터 로드 시도
        try {
            const response = await fetch('data/drawings.json');
            const drawings = await response.json();
            
            // 데이터 분석
            const totalDocs = drawings.length;
            const uniqueProjects = new Set(drawings.map(d => d.contractor_dwg_no.split('-')[0])).size;
            const recent = drawings.slice(0, 5).map(d => ({
                type: 'create',
                title: d.title,
                description: `${d.shop_dwg_no} - ${d.status}`,
                created_at: new Date().toISOString() // 임시 날짜
            }));

            return {
                success: true,
                data: {
                    projects: uniqueProjects,
                    documents: totalDocs,
                    recent_uploads: 12
                },
                activities: recent
            };
        } catch (e) {
            console.error('JSON 로드 실패:', e);
            return {
                success: true,
                data: { projects: 0, documents: 0, recent_uploads: 0 },
                activities: []
            };
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-title">${icons[type]} ${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        // 토스트 컨테이너 확인/생성
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // 애니메이션
        setTimeout(() => toast.classList.add('show'), 100);
        
        // 자동 제거
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.sstdmsApp = new SSTDMSMobileApp();
});

// 전역 에러 핸들링
window.addEventListener('error', (e) => {
    console.error('전역 에러:', e.error);
    if (window.sstdmsApp) {
        window.sstdmsApp.showToast('오류가 발생했습니다', 'error');
    }
});

// 전역 Promise 에러 핸들링
window.addEventListener('unhandledrejection', (e) => {
    console.error('처리되지 않은 Promise 에러:', e.reason);
    if (window.sstdmsApp) {
        window.sstdmsApp.showToast('네트워크 오류가 발생했습니다', 'error');
    }
});

