(() => {
  const catalog = {tr: {}, ru: {}, modules: {}};
  const initialLanguage = localStorage.getItem('cpp-adventure-language') === 'ru' ? 'ru' : 'tr';
  const state = {
    catalog,
    language: initialLanguage,
    ready: fetch('/locales.json', {cache: 'no-store'})
      .then(response => {
        if (!response.ok) throw new Error(`Locale catalog HTTP ${response.status}`);
        return response.json();
      })
      .then(data => {
        if (!data?.tr || !data?.ru || !data?.modules) throw new Error('Locale catalog is incomplete');
        Object.assign(catalog, data);
        document.documentElement.lang = state.language;
        return catalog;
      }),
    setLanguage(language) {
      this.language = language === 'ru' ? 'ru' : 'tr';
      document.documentElement.lang = this.language;
      return this.language;
    },
    module(name, language = this.language) {
      const value = catalog.modules?.[name];
      return value?.[language] ?? value ?? {};
    },
    t(path, language = this.language) {
      const parts = String(path).split('.');
      let value;
      if (parts[0] === 'modules') {
        value = catalog;
        for (const part of parts) value = value?.[part];
      } else if (Object.hasOwn(catalog, parts[0])) {
        value = catalog;
        for (const part of parts) value = value?.[part];
      } else {
        const moduleName = parts.shift();
        value = catalog.modules?.[moduleName];
        if (moduleName === 'pairs') {
          value = value?.[parts.join('.')];
          parts.length = 0;
        }
        if (value && Object.hasOwn(value, 'tr') && Object.hasOwn(value, 'ru')) value = value[language];
        for (const part of parts) value = value?.[part];
      }
      if (value && typeof value === 'object' && !Array.isArray(value)) value = value[language];
      return typeof value === 'string' ? value : String(path);
    },
    format(path, values = {}, language = this.language) {
      return this.t(path, language).replace(/\{([a-zA-Z0-9_]+)\}/g, (token, key) =>
        Object.hasOwn(values, key) ? String(values[key]) : token
      );
    },
    audit() {
      const mismatches = [];
      const compare = (left, right, prefix) => {
        if (typeof left === 'string' || typeof right === 'string') {
          if (typeof left !== 'string' || !left.trim() || typeof right !== 'string' || !right.trim()) mismatches.push(prefix);
          return;
        }
        if (Array.isArray(left) || Array.isArray(right)) {
          if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) { mismatches.push(`${prefix}.length`); return; }
          left.forEach((value, index) => {
            const other = right[index], path = `${prefix}.${index}`;
            if (value && other && typeof value === 'object' && typeof other === 'object') compare(value, other, path);
            else if (typeof value !== 'string' || !value.trim() || typeof other !== 'string' || !other.trim()) mismatches.push(path);
          });
          return;
        }
        const a = Object.keys(left || {}).sort(), b = Object.keys(right || {}).sort();
        for (const key of [...new Set([...a, ...b])]) {
          if (!Object.hasOwn(left || {}, key) || !Object.hasOwn(right || {}, key)) mismatches.push(`${prefix}.${key}`);
          else if (left[key] && right[key] && typeof left[key] === 'object' && typeof right[key] === 'object') compare(left[key], right[key], `${prefix}.${key}`);
          else if (typeof left[key] !== 'string' || typeof right[key] !== 'string' || !left[key].trim() || !right[key].trim()) mismatches.push(`${prefix}.${key}`);
        }
      };
      compare(catalog.tr, catalog.ru, 'core');
      for (const [name, translations] of Object.entries(catalog.modules || {})) {
        if (name === 'pairs' || name === 'worldZones') continue;
        compare(translations.tr, translations.ru, name);
      }
      for (const [name, translations] of Object.entries(catalog.modules?.pairs || {})) {
        compare(translations.tr, translations.ru, `pairs.${name}`);
      }
      const zonesTr = catalog.modules?.worldZones?.tr || [];
      const zonesRu = catalog.modules?.worldZones?.ru || [];
      if (!Array.isArray(zonesTr) || !Array.isArray(zonesRu) || zonesTr.length !== zonesRu.length) mismatches.push('worldZones.length');
      else zonesTr.forEach((value, index) => { if (typeof value !== 'string' || !value.trim() || typeof zonesRu[index] !== 'string' || !zonesRu[index].trim()) mismatches.push(`worldZones.${index}`); });
      return {ok: mismatches.length === 0, mismatch_count: mismatches.length, mismatches};
    }
  };
  window.CppAdventureI18n = state;
  window.L = (path, values) => state.format(path, values);
  const I18N = catalog;
  const localizedProxy = name => ({get tr(){return catalog.modules?.[name]?.tr || {}}, get ru(){return catalog.modules?.[name]?.ru || {}}});
  const SHOP_TEXT = localizedProxy('shop');
  const EXTRA_TEXT = localizedProxy('extra');
  const DEVTOOLS_TEXT = localizedProxy('devtools');
  const AI_COPY = localizedProxy('ai');
  const ex = key => state.t(`modules.extra.${state.language}.${key}`);
  const dt = key => state.t(`modules.devtools.${state.language}.${key}`);
  const aiText = key => state.t(`modules.ai.${state.language}.${key}`);
  window.I18N = I18N;
  window.SHOP_TEXT = SHOP_TEXT;
  window.EXTRA_TEXT = EXTRA_TEXT;
  window.DEVTOOLS_TEXT = DEVTOOLS_TEXT;
  window.AI_COPY = AI_COPY;
  window.ex = ex;
  window.dt = dt;
  window.aiText = aiText;
})();
