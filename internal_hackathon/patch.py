import json
import os

base_dir = r'c:\Users\MANIKANTA\Downloads\kisansetu\SIH2026-WorksInProduction\internal_hackathon\apps\farmer-pwa\src'

new_keys_en = {
    'menu.markets': 'Nearby markets',
    'menu.markets.sub': 'Compare before selling',
    'menu.markets.sub2': 'Compare today’s options',
    'menu.copilot': 'Support copilot',
    'menu.copilot.sub': 'Ask about your status',
    'menu.privacy': 'Privacy & consent',
    'menu.privacy.sub': 'Control how information is used',
    'menu.privacy.subtitle': 'Your choices stay editable',
    'profile.title': 'Your support space',
    'profile.score': 'Support score',
    'profile.confidence': 'Confidence',
    'markets.priceOptions': 'PRICE OPTIONS',
    'markets.nearYou': 'Markets near you',
    'markets.compare': 'Compare, then confirm',
    'markets.compareSub': 'Your FPO or officer confirms availability and grade before you travel.',
    'support.network': 'KisanSetu support network',
    'support.networkSub': 'Your score is for support prioritisation, never for credit or insurance decisions.'
}

new_keys_hi = {
    'menu.markets': 'आसपास की मंडियां',
    'menu.markets.sub': 'बेचने से पहले तुलना करें',
    'menu.markets.sub2': 'आज के विकल्पों की तुलना करें',
    'menu.copilot': 'सपोर्ट कोपायलट',
    'menu.copilot.sub': 'अपनी स्थिति के बारे में पूछें',
    'menu.privacy': 'गोपनीयता और सहमति',
    'menu.privacy.sub': 'नियंत्रित करें कि जानकारी का उपयोग कैसे किया जाता है',
    'menu.privacy.subtitle': 'आपकी पसंद संपादन योग्य रहती है',
    'profile.title': 'आपका सपोर्ट स्पेस',
    'profile.score': 'सपोर्ट स्कोर',
    'profile.confidence': 'विश्वास',
    'markets.priceOptions': 'मूल्य विकल्प',
    'markets.nearYou': 'आपके पास की मंडियां',
    'markets.compare': 'तुलना करें, फिर पुष्टि करें',
    'markets.compareSub': 'आपका एफपीओ या अधिकारी यात्रा करने से पहले पुष्टि करता है।',
    'support.network': 'किसानसेतु सपोर्ट नेटवर्क',
    'support.networkSub': 'आपका स्कोर सहायता के लिए है, ऋण या बीमा के लिए नहीं।'
}

new_keys_pa = {
    'menu.markets': 'ਨੇੜਲੀਆਂ ਮੰਡੀਆਂ',
    'menu.markets.sub': 'ਵੇਚਣ ਤੋਂ ਪਹਿਲਾਂ ਤੁਲਨਾ ਕਰੋ',
    'menu.markets.sub2': 'ਅੱਜ ਦੇ ਵਿਕਲਪਾਂ ਦੀ ਤੁਲਨਾ ਕਰੋ',
    'menu.copilot': 'ਸਹਾਇਤਾ ਕੋਪਾਇਲਟ',
    'menu.copilot.sub': 'ਆਪਣੀ ਸਥਿਤੀ ਬਾਰੇ ਪੁੱਛੋ',
    'menu.privacy': 'ਗੋਪਨੀਯਤਾ ਅਤੇ ਸਹਿਮਤੀ',
    'menu.privacy.sub': 'ਜਾਣਕਾਰੀ ਦੀ ਵਰਤੋਂ ਨੂੰ ਕੰਟਰੋਲ ਕਰੋ',
    'menu.privacy.subtitle': 'ਤੁਹਾਡੀਆਂ ਚੋਣਾਂ ਬਦਲੀਆਂ ਜਾ ਸਕਦੀਆਂ ਹਨ',
    'profile.title': 'ਤੁਹਾਡਾ ਸਹਾਇਤਾ ਸਥਾਨ',
    'profile.score': 'ਸਹਾਇਤਾ ਸਕੋਰ',
    'profile.confidence': 'ਭਰੋਸਾ',
    'markets.priceOptions': 'ਕੀਮਤ ਵਿਕਲਪ',
    'markets.nearYou': 'ਤੁਹਾਡੇ ਨੇੜੇ ਦੀਆਂ ਮੰਡੀਆਂ',
    'markets.compare': 'ਤੁਲਨਾ ਕਰੋ, ਫਿਰ ਪੁਸ਼ਟੀ ਕਰੋ',
    'markets.compareSub': 'ਯਾਤਰਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਅਧਿਕਾਰੀ ਪੁਸ਼ਟੀ ਕਰਦਾ ਹੈ।',
    'support.network': 'ਕਿਸਾਨਸੇਤੁ ਸਹਾਇਤਾ ਨੈੱਟਵਰਕ',
    'support.networkSub': 'ਤੁਹਾਡਾ ਸਕੋਰ ਸਹਾਇਤਾ ਲਈ ਹੈ, ਕਰਜ਼ੇ ਜਾਂ ਬੀਮੇ ਲਈ ਨਹੀਂ।'
}

for lang, new_keys in [('en', new_keys_en), ('hi', new_keys_hi), ('mr', new_keys_pa)]:
    path = os.path.join(base_dir, f'i18n/{lang}.json')
    with open(path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    data.update(new_keys)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
