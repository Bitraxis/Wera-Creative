from browser import document, window

def scroll_to_contact(ev=None):
    contact = document.getElementById('contact')
    if contact:
        contact.scrollIntoView({'behavior':'smooth'})

# header contact link should scroll instead of navigating away
nav_contact = document.getElementById('nav__a4')
if nav_contact:
    def nav_click(ev):
        ev.preventDefault()
        scroll_to_contact(ev)
    nav_contact.bind('click', nav_click)

# attach to card buttons
for btn in document.select('.card__contact-btn'):
    def make_handler(b):
        def _handler(ev):
            ev.preventDefault()
            scroll_to_contact(ev)
        return _handler
    btn.bind('click', make_handler(btn))

# Quote toggling: hover or click toggles between two quotes and persists until toggled again
quotes = [
    {"text": "To som v živote nerobila, to mi určite pôjde!", "author": "Neznámy autor"},
    {"text": "Som presvedčená, že každý svojím konaním ovplyvňuje svoje smerovanie, svoju budúcnosť.", "author": "Neznámy autor"}
]

quote_el = document.getElementById('hero-quote')
quote_text = quote_el.select_one('.quote__text') if quote_el else None
quote_author = quote_el.select_one('.quote__author') if quote_el else None

current_idx = 0
def update_quote(idx):
    global current_idx
    current_idx = idx
    if quote_text:
        quote_text.text = quotes[idx]['text']
    if quote_author:
        quote_author.text = quotes[idx]['author']

def toggle_quote(ev=None):
    # crossfade: add fade-out, update after timeout, then fade back in
    if not quote_el:
        return
    # prevent re-entrancy
    if 'fade-out' in quote_el.classList:
        return
    new_idx = 1 - current_idx
    # start fade-out
    quote_el.classList.add('fade-out')

def finish():
    update_quote(new_idx)
    quote_el.classList.remove('fade-out')

    # wait for CSS fade-out to complete (~280ms), then swap and fade-in
window.setTimeout(finish, 300)

if quote_el:
    # bind mouseenter and click so desktop hover or touch/click toggles
    quote_el.bind('mouseenter', toggle_quote)
    quote_el.bind('click', toggle_quote)

    # keyboard support: Enter or Space toggles when focused
def key_handler(ev):
    if ev.key in ('Enter', ' '):
        ev.preventDefault()
        toggle_quote(ev)
quote_el.bind('keydown', key_handler)

    # ensure initial content
update_quote(current_idx)