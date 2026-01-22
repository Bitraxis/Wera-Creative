(function(){
    function initLangSwitch(){
        const buttons = Array.from(document.querySelectorAll('.filters .filter'));
        const cards = Array.from(document.querySelectorAll('.cards-grid .card'));

        function setLang(lang){
            buttons.forEach(btn => {
                const isActive = btn.dataset.lang === lang;
                btn.classList.toggle('active', isActive);
                btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });
            cards.forEach(card => {
                const sk = card.querySelector('.card__sk');
                const de = card.querySelector('.card__de');
                if(sk) sk.hidden = (lang !== 'sk');
                if(de) de.hidden = (lang !== 'de');
            });
        }

        if(buttons.length === 0) return;

        buttons.forEach(btn => {
            btn.addEventListener('click', () => setLang(btn.dataset.lang));
            btn.addEventListener('keydown', (e) => {
                if(e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setLang(btn.dataset.lang);
                }
            });
        });

          // initialise: prefer an already-marked active button, otherwise default to 'sk'
        const activeBtn = buttons.find(b => b.classList.contains('active'));
        setLang(activeBtn ? activeBtn.dataset.lang : 'sk');
    }

    function initCardToFormSelection(){
        const serviceSelect = document.querySelector('#service');
        const buttons = Array.from(document.querySelectorAll('.card__contact-btn'));
        if(!serviceSelect || buttons.length === 0) return;

        buttons.forEach(btn => {
            const targetValue = btn.id;
            if(!targetValue) return;
            btn.addEventListener('click', () => {
                const option = serviceSelect.querySelector(`option[value="${targetValue}"]`);
                if(option){
                    serviceSelect.value = targetValue;
                    serviceSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
                const form = document.querySelector('.contact__form');
                if(form){
                    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    function init(){
        initLangSwitch();
        initCardToFormSelection();
    }

    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();