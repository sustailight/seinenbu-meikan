document.addEventListener('DOMContentLoaded', () => {
    // もっと見るボタン (その場で展開するインライン開閉)
    const textClamps = document.querySelectorAll('.js-text-clamp');

    textClamps.forEach(clamp => {
        // コンテンツがコンテナより大きい場合にもっと見るボタンを表示
        if (clamp.scrollHeight > clamp.clientHeight) {
            const btn = clamp.nextElementSibling;
            if (btn && btn.classList.contains('js-more-btn')) {
                btn.style.display = 'inline-block';
                btn.addEventListener('click', () => {
                    const isExpanded = clamp.classList.toggle('is-expanded');
                    if (isExpanded) {
                        btn.textContent = '閉じる';
                    } else {
                        btn.textContent = 'もっと見る';
                    }
                });
            }
        }
    });

    // ニックネームの文字サイズ自動縮小（画像枠に収めるため）
    const fitTexts = document.querySelectorAll('.js-fit-text');
    fitTexts.forEach(el => {
        const parent = el.parentElement;
        // 余白を考慮した最大幅
        const parentWidth = parent.clientWidth - parseInt(window.getComputedStyle(parent).paddingLeft||0) - Math.abs(parseInt(window.getComputedStyle(parent).paddingRight||0)) - 10;
        let fontSize = parseInt(window.getComputedStyle(el).fontSize);
        
        while (el.scrollWidth > parentWidth && fontSize > 10) {
            fontSize--;
            el.style.fontSize = fontSize + 'px';
        }
    });

    // FV（最初の画面）のリンクをクリックしたときのスムーズスクロール
    const memberLinks = document.querySelectorAll('.member-link');
    memberLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // スムーズスクロール & 上下ナビゲーションボタン機能
    const navUp = document.getElementById('nav-up');
    const navDown = document.getElementById('nav-down');
    const container = document.getElementById('scroll-container');
    const panels = Array.from(document.querySelectorAll('.index-section, .member-slide'));

    if (container && panels.length > 0) {
        // 現在表示されているパネルのインデックスを取得
        const getCurrentIndex = () => {
            let index = 0;
            let minDistance = Infinity;
            const containerCenter = container.getBoundingClientRect().top + container.clientHeight / 2;

            panels.forEach((panel, i) => {
                const rect = panel.getBoundingClientRect();
                const panelCenter = rect.top + rect.height / 2;
                const distance = Math.abs(containerCenter - panelCenter);
                if (distance < minDistance) {
                    minDistance = distance;
                    index = i;
                }
            });
            return index;
        };

        const updateButtons = () => {
            const currentIndex = getCurrentIndex();
            
            // 一番上（index-section）なら
            if (currentIndex === 0) {
                navUp.classList.add('hidden'); // トップでは「戻る」不可
            } else if (currentIndex === 1) {
                navUp.classList.remove('hidden');
                navUp.innerHTML = '▲<br>TOP'; // 1人目ならトップへ
            } else {
                navUp.classList.remove('hidden');
                navUp.innerHTML = '▲<br>戻る';
            }

            // 一番下なら
            if (currentIndex === panels.length - 1) {
                navDown.classList.add('hidden');
            } else {
                navDown.classList.remove('hidden');
            }
        };

        // スクロール時にボタン状態を更新 (スナップが終わる頃に発火)
        let scrollTimeout;
        container.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(updateButtons, 100);
        });

        // ボタンクリック機能
        if(navUp) {
            navUp.addEventListener('click', () => {
                const currentIndex = getCurrentIndex();
                if (currentIndex > 0) {
                    panels[currentIndex - 1].scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }

        if(navDown) {
            navDown.addEventListener('click', () => {
                const currentIndex = getCurrentIndex();
                if (currentIndex < panels.length - 1) {
                    panels[currentIndex + 1].scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }

        // 初期状態でボタンを更新
        setTimeout(updateButtons, 300); // レイアウト完了後に実行
    }
});
