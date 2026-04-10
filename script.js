document.addEventListener('DOMContentLoaded', () => {
    // ---- 「もっと見る」ボタンの動的表示制御 ----
    const clamps = document.querySelectorAll('.js-text-clamp');
    
    clamps.forEach(clamp => {
        // 実際のテキスト高さ(scrollHeight)が設定された高さ(clientHeight)を超えている場合のみ
        // つまり、webkit-line-clampで文字が切り捨てられている場合のみボタンを表示する
        if (clamp.scrollHeight > clamp.clientHeight) {
            const btn = clamp.nextElementSibling;
            if (btn && btn.classList.contains('js-more-btn')) {
                btn.style.display = 'inline-block'; // ボタンを表示
                
                // ボタンクリック時にモーダルを開く
                btn.addEventListener('click', () => {
                    const sectionTitle = clamp.previousElementSibling.textContent;
                    const fullText = clamp.getAttribute('data-fulltext');
                    openModal(sectionTitle, fullText);
                });
            }
        }
    });

    // ---- モーダル関連の処理 ----
    const modal = document.getElementById('text-modal');
    const modalClose = document.querySelector('.js-modal-close');
    const modalTitle = document.querySelector('.js-modal-title');
    const modalBody = document.querySelector('.js-modal-body');

    function openModal(title, text) {
        modalTitle.textContent = title;
        modalBody.textContent = text;
        modal.classList.add('is-active');
    }

    function closeModal() {
        modal.classList.remove('is-active');
    }

    // バツボタンクリックで閉じる
    modalClose.addEventListener('click', closeModal);

    // モーダルの背景枠外クリックで閉じる
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
});
