// Napoleonic factions data — 6 powers, drawn from historical 1803-1815 conflicts.
// Heraldry rendered as inline SVG so it scales crisply at any size.

const FACTIONS = {
  france: {
    id: 'france',
    name: '法兰西帝国',
    nameEn: 'Empire Français',
    motto: 'Liberté · Égalité · Fraternité',
    primary: '#1e3a6f',     // bleu de France
    accent: '#c8102e',       // rouge
    gold: '#d4a55c',
    canvas: '#e8d8b8',
    leader: '拿破仑·波拿巴',
    leaderTitle: 'Empereur',
    crest: (size = 60) => `
      <svg viewBox="0 0 60 60" width="${size}" height="${size}">
        <defs>
          <radialGradient id="fr-gold" cx="0.3" cy="0.3">
            <stop offset="0" stop-color="#f5d889"/>
            <stop offset="1" stop-color="#b8862e"/>
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="28" fill="#1e3a6f" stroke="url(#fr-gold)" stroke-width="1.5"/>
        <!-- imperial eagle silhouette -->
        <g fill="url(#fr-gold)" transform="translate(30,32)">
          <path d="M0,-14 C-3,-12 -5,-9 -5,-5 L-12,-3 L-14,2 L-9,1 L-12,5 L-7,5 L-10,9 L-3,7 L-2,11 L0,8 L2,11 L3,7 L10,9 L7,5 L12,5 L9,1 L14,2 L12,-3 L5,-5 C5,-9 3,-12 0,-14 Z"/>
          <circle cx="0" cy="-9" r="1.5" fill="#1e3a6f"/>
        </g>
        <text x="30" y="55" text-anchor="middle" font-size="6" fill="url(#fr-gold)" font-family="serif" letter-spacing="1">N</text>
      </svg>`,
    flag: (w = 60, h = 40) => `
      <svg viewBox="0 0 60 40" width="${w}" height="${h}">
        <rect x="0" y="0" width="20" height="40" fill="#1e3a6f"/>
        <rect x="20" y="0" width="20" height="40" fill="#f4f1e8"/>
        <rect x="40" y="0" width="20" height="40" fill="#c8102e"/>
      </svg>`,
  },

  britain: {
    id: 'britain',
    name: '大不列颠',
    nameEn: 'United Kingdom',
    motto: 'Dieu et mon droit',
    primary: '#8b1a1a',
    accent: '#d4a55c',
    gold: '#d4a55c',
    canvas: '#e8dcc4',
    leader: '威灵顿公爵',
    leaderTitle: 'Field Marshal',
    crest: (size = 60) => `
      <svg viewBox="0 0 60 60" width="${size}" height="${size}">
        <defs>
          <radialGradient id="br-gold" cx="0.3" cy="0.3">
            <stop offset="0" stop-color="#f5d889"/>
            <stop offset="1" stop-color="#b8862e"/>
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="28" fill="#8b1a1a" stroke="url(#br-gold)" stroke-width="1.5"/>
        <!-- crown + lion -->
        <g fill="url(#br-gold)" transform="translate(30,32)">
          <path d="M-10,-8 L-7,-12 L-3,-9 L0,-13 L3,-9 L7,-12 L10,-8 L10,-5 L-10,-5 Z"/>
          <circle cx="-7" cy="-12" r="1"/><circle cx="0" cy="-13" r="1"/><circle cx="7" cy="-12" r="1"/>
          <path d="M-9,-3 L9,-3 L7,8 L4,11 L-4,11 L-7,8 Z" stroke="#8b1a1a" stroke-width="0.4"/>
          <text x="0" y="6" text-anchor="middle" font-size="7" fill="#8b1a1a" font-family="serif" font-weight="bold">G</text>
        </g>
      </svg>`,
    flag: (w = 60, h = 40) => `
      <svg viewBox="0 0 60 40" width="${w}" height="${h}">
        <rect width="60" height="40" fill="#012169"/>
        <path d="M0,0 L60,40 M60,0 L0,40" stroke="#fff" stroke-width="6"/>
        <path d="M0,0 L60,40 M60,0 L0,40" stroke="#c8102e" stroke-width="3"/>
        <path d="M30,0 V40 M0,20 H60" stroke="#fff" stroke-width="10"/>
        <path d="M30,0 V40 M0,20 H60" stroke="#c8102e" stroke-width="6"/>
      </svg>`,
  },

  prussia: {
    id: 'prussia',
    name: '普鲁士王国',
    nameEn: 'Königreich Preußen',
    motto: 'Suum cuique',
    primary: '#1a1a1a',
    accent: '#c0c0c0',
    gold: '#b8a06e',
    canvas: '#dcd6c8',
    leader: '布吕歇尔元帅',
    leaderTitle: 'Generalfeldmarschall',
    crest: (size = 60) => `
      <svg viewBox="0 0 60 60" width="${size}" height="${size}">
        <defs>
          <radialGradient id="pr-silver" cx="0.3" cy="0.3">
            <stop offset="0" stop-color="#e8e8e8"/>
            <stop offset="1" stop-color="#888"/>
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="28" fill="#1a1a1a" stroke="url(#pr-silver)" stroke-width="1.5"/>
        <!-- iron cross -->
        <g fill="url(#pr-silver)" transform="translate(30,30)">
          <path d="M-3,-14 L3,-14 L3,-3 L14,-3 L14,3 L3,3 L3,14 L-3,14 L-3,3 L-14,3 L-14,-3 L-3,-3 Z" stroke="#000" stroke-width="0.5"/>
        </g>
      </svg>`,
    flag: (w = 60, h = 40) => `
      <svg viewBox="0 0 60 40" width="${w}" height="${h}">
        <rect width="60" height="40" fill="#f4f1e8"/>
        <g transform="translate(30,20)">
          <path d="M-12,-2 L-3,-2 L-3,-11 L3,-11 L3,-2 L12,-2 L12,2 L3,2 L3,11 L-3,11 L-3,2 L-12,2 Z" fill="#1a1a1a"/>
        </g>
      </svg>`,
  },

  russia: {
    id: 'russia',
    name: '俄罗斯帝国',
    nameEn: 'Российская Империя',
    motto: 'С нами Бог',
    primary: '#1c4a2e',
    accent: '#d4a55c',
    gold: '#d4a55c',
    canvas: '#dccfb4',
    leader: '库图佐夫元帅',
    leaderTitle: 'Генерал-фельдмаршал',
    crest: (size = 60) => `
      <svg viewBox="0 0 60 60" width="${size}" height="${size}">
        <defs>
          <radialGradient id="ru-gold" cx="0.3" cy="0.3">
            <stop offset="0" stop-color="#f5d889"/>
            <stop offset="1" stop-color="#b8862e"/>
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="28" fill="#1c4a2e" stroke="url(#ru-gold)" stroke-width="1.5"/>
        <!-- double-headed eagle (simplified) -->
        <g fill="url(#ru-gold)" transform="translate(30,32)">
          <ellipse cx="0" cy="2" rx="9" ry="11"/>
          <path d="M-4,-8 C-6,-12 -8,-12 -8,-8 L-7,-5 L-4,-6 Z"/>
          <path d="M4,-8 C6,-12 8,-12 8,-8 L7,-5 L4,-6 Z"/>
          <path d="M-13,3 L-9,0 L-7,5 Z M13,3 L9,0 L7,5 Z"/>
          <circle cx="-6" cy="-7" r="1" fill="#1c4a2e"/><circle cx="6" cy="-7" r="1" fill="#1c4a2e"/>
        </g>
      </svg>`,
    flag: (w = 60, h = 40) => `
      <svg viewBox="0 0 60 40" width="${w}" height="${h}">
        <rect y="0" width="60" height="13.3" fill="#f4f1e8"/>
        <rect y="13.3" width="60" height="13.3" fill="#0033a0"/>
        <rect y="26.6" width="60" height="13.4" fill="#c8102e"/>
      </svg>`,
  },

  austria: {
    id: 'austria',
    name: '奥地利帝国',
    nameEn: 'Kaisertum Österreich',
    motto: 'A.E.I.O.U.',
    primary: '#5a1a1a',
    accent: '#d4a55c',
    gold: '#d4a55c',
    canvas: '#e0d2b4',
    leader: '卡尔大公',
    leaderTitle: 'Erzherzog',
    crest: (size = 60) => `
      <svg viewBox="0 0 60 60" width="${size}" height="${size}">
        <defs>
          <radialGradient id="au-gold" cx="0.3" cy="0.3">
            <stop offset="0" stop-color="#f5d889"/>
            <stop offset="1" stop-color="#b8862e"/>
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="28" fill="#5a1a1a" stroke="url(#au-gold)" stroke-width="1.5"/>
        <!-- shield with bend -->
        <g transform="translate(30,30)">
          <path d="M-11,-12 L11,-12 L11,4 C11,9 6,13 0,14 C-6,13 -11,9 -11,4 Z" fill="#f4f1e8"/>
          <rect x="-11" y="-3" width="22" height="6" fill="#c8102e"/>
          <path d="M-11,-12 L11,-12 L11,4 C11,9 6,13 0,14 C-6,13 -11,9 -11,4 Z" fill="none" stroke="url(#au-gold)" stroke-width="1.2"/>
        </g>
      </svg>`,
    flag: (w = 60, h = 40) => `
      <svg viewBox="0 0 60 40" width="${w}" height="${h}">
        <rect y="0" width="60" height="13.3" fill="#c8102e"/>
        <rect y="13.3" width="60" height="13.3" fill="#f4f1e8"/>
        <rect y="26.6" width="60" height="13.4" fill="#c8102e"/>
      </svg>`,
  },

  spain: {
    id: 'spain',
    name: '西班牙王国',
    nameEn: 'Reino de España',
    motto: 'Plus Ultra',
    primary: '#a8200d',
    accent: '#d4a55c',
    gold: '#d4a55c',
    canvas: '#e6d4b4',
    leader: '卡斯塔尼奥斯',
    leaderTitle: 'General',
    crest: (size = 60) => `
      <svg viewBox="0 0 60 60" width="${size}" height="${size}">
        <defs>
          <radialGradient id="sp-gold" cx="0.3" cy="0.3">
            <stop offset="0" stop-color="#f5d889"/>
            <stop offset="1" stop-color="#b8862e"/>
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="28" fill="#a8200d" stroke="url(#sp-gold)" stroke-width="1.5"/>
        <!-- castle + lion quartered shield -->
        <g transform="translate(30,30)">
          <path d="M-12,-12 L12,-12 L12,4 C12,10 6,14 0,15 C-6,14 -12,10 -12,4 Z" fill="#f4f1e8" stroke="url(#sp-gold)" stroke-width="1"/>
          <line x1="0" y1="-12" x2="0" y2="15" stroke="url(#sp-gold)" stroke-width="0.6"/>
          <line x1="-12" y1="0" x2="12" y2="0" stroke="url(#sp-gold)" stroke-width="0.6"/>
          <!-- castle -->
          <g fill="#a8200d" transform="translate(-6,-6)">
            <rect x="-3" y="-3" width="6" height="6"/>
            <rect x="-4" y="-4" width="2" height="1.5"/><rect x="-1" y="-4" width="2" height="1.5"/><rect x="2" y="-4" width="2" height="1.5"/>
          </g>
          <!-- lion -->
          <g fill="#5a1a1a" transform="translate(6,-6)">
            <path d="M-3,2 L-3,-2 L-2,-3 L2,-3 L3,-1 L3,2 Z"/>
            <circle cx="-2" cy="-2" r="0.8"/>
          </g>
        </g>
      </svg>`,
    flag: (w = 60, h = 40) => `
      <svg viewBox="0 0 60 40" width="${w}" height="${h}">
        <rect y="0" width="60" height="10" fill="#a8200d"/>
        <rect y="10" width="60" height="20" fill="#f1bf00"/>
        <rect y="30" width="60" height="10" fill="#a8200d"/>
      </svg>`,
  },
};

// Card archetypes — historically grounded
const UNIT_TYPES = {
  infantry:   { id: 'infantry',   name: '战列步兵',  icon: '⚔', tint: '#8fb0c5' },
  skirmisher: { id: 'skirmisher', name: '散兵',     icon: '✦', tint: '#8daf64' },
  cavalry:    { id: 'cavalry',    name: '骑兵',     icon: '⚞', tint: '#c06a5b' },
  artillery:  { id: 'artillery',  name: '炮兵',     icon: '◉', tint: '#b79a4a' },
  guard:      { id: 'guard',      name: '近卫',     icon: '★', tint: '#9f75bd' },
  command:    { id: 'command',    name: '军令',     icon: '⌘', tint: '#d4a55c' },
};

// Active simulator decks. France, Prussia, and Russia mirror
// prototypes/card-battle-sim/cards.py. Extra factions below are retained as
// visual references for future expansion and are not used by the default app.
const FACTION_DECKS = {
  france: [
    { name: '猎兵连', type: 'skirmisher', cost: 1, atk: 1, hp: 2, kw: '闪避' },
    { name: '猎兵连', type: 'skirmisher', cost: 1, atk: 1, hp: 2, kw: '闪避' },
    { name: '猎兵连', type: 'skirmisher', cost: 1, atk: 1, hp: 2, kw: '闪避' },
    { name: '第45线列步兵团', type: 'infantry', cost: 3, atk: 3, hp: 4, kw: '结阵、齐射' },
    { name: '第45线列步兵团', type: 'infantry', cost: 3, atk: 3, hp: 4, kw: '结阵、齐射' },
    { name: '第45线列步兵团', type: 'infantry', cost: 3, atk: 3, hp: 4, kw: '结阵、齐射' },
    { name: '第45线列步兵团', type: 'infantry', cost: 3, atk: 3, hp: 4, kw: '结阵、齐射' },
    { name: '近卫掷弹兵', type: 'infantry', cost: 5, atk: 5, hp: 5, kw: '结阵、齐射、守卫' },
    { name: '近卫掷弹兵', type: 'infantry', cost: 5, atk: 5, hp: 5, kw: '结阵、齐射、守卫' },
    { name: '龙骑兵团', type: 'cavalry', cost: 4, atk: 3, hp: 3, kw: '冲锋' },
    { name: '龙骑兵团', type: 'cavalry', cost: 4, atk: 3, hp: 3, kw: '冲锋' },
    { name: '龙骑兵团', type: 'cavalry', cost: 4, atk: 3, hp: 3, kw: '冲锋' },
    { name: '胸甲骑兵', type: 'cavalry', cost: 6, atk: 6, hp: 5, kw: '冲锋、突破' },
    { name: '近卫马炮兵', type: 'artillery', cost: 4, atk: 3, hp: 3, kw: '远程、阿尔科莱精神、军团联动' },
    { name: '近卫马炮兵', type: 'artillery', cost: 4, atk: 3, hp: 3, kw: '远程、阿尔科莱精神、军团联动' },
    { name: '12磅野战炮', type: 'artillery', cost: 5, atk: 4, hp: 3, kw: '远程' },
    { name: '12磅野战炮', type: 'artillery', cost: 5, atk: 4, hp: 3, kw: '远程' },
    { name: '老近卫军', type: 'guard', cost: 8, atk: 6, hp: 8, kw: '结阵、齐射、守卫、突破' },
    { name: '骠骑兵', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、侧翼迂回' },
    { name: '骠骑兵', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、侧翼迂回' },
    { name: '骠骑兵', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、侧翼迂回' },
    { name: '征召步兵营', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵' },
    { name: '征召步兵营', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵' },
    { name: '征召步兵营', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵' },
    { name: '帝国步兵团', type: 'infantry', cost: 4, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '帝国步兵团', type: 'infantry', cost: 4, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '帝国步兵团', type: 'infantry', cost: 4, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '帝国步兵团', type: 'infantry', cost: 4, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '达武的铁军', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'fortify_target_INF_GUARD+0+2_guard' },
    { name: '奥斯特里茨晨雾', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'weather_fog_artillery-1' },
  ],
  britain: [
    { name: '苏格兰灰骑兵', type: 'cavalry',  cost: 5, atk: 4, hp: 5, kw: '冲锋' },
    { name: '红衫军',       type: 'infantry', cost: 3, atk: 4, hp: 3, kw: '齐射' },
    { name: '步枪团',       type: 'skirmisher', cost: 3, atk: 3, hp: 2, kw: '远程' },
    { name: '皇家炮兵',     type: 'artillery', cost: 4, atk: 4, hp: 3, kw: '远程' },
    { name: '威灵顿',       type: 'guard',    cost: 7, atk: 5, hp: 8, kw: '指挥' },
    { name: '掷弹兵卫队',   type: 'guard',    cost: 6, atk: 5, hp: 6, kw: '坚毅' },
  ],
  prussia: [
    { name: '耶格猎兵', type: 'skirmisher', cost: 1, atk: 2, hp: 2, kw: '闪避、齐射' },
    { name: '耶格猎兵', type: 'skirmisher', cost: 1, atk: 2, hp: 2, kw: '闪避、齐射' },
    { name: '耶格猎兵', type: 'skirmisher', cost: 1, atk: 2, hp: 2, kw: '闪避、齐射' },
    { name: '西里西亚国民军', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵' },
    { name: '西里西亚国民军', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵' },
    { name: '西里西亚国民军', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵' },
    { name: '普鲁士线列军', type: 'infantry', cost: 3, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '普鲁士线列军', type: 'infantry', cost: 3, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '普鲁士线列军', type: 'infantry', cost: 3, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '普鲁士线列军', type: 'infantry', cost: 3, atk: 4, hp: 4, kw: '结阵、齐射' },
    { name: '近卫掷弹兵团', type: 'infantry', cost: 4, atk: 4, hp: 5, kw: '结阵、齐射、守卫' },
    { name: '近卫掷弹兵团', type: 'infantry', cost: 4, atk: 4, hp: 5, kw: '结阵、齐射、守卫' },
    { name: '近卫掷弹兵团', type: 'infantry', cost: 4, atk: 4, hp: 5, kw: '结阵、齐射、守卫' },
    { name: '死骑兵', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、死神威慑' },
    { name: '死骑兵', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、死神威慑' },
    { name: '死骑兵', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、死神威慑' },
    { name: '普鲁士龙骑', type: 'cavalry', cost: 4, atk: 4, hp: 3, kw: '冲锋' },
    { name: '普鲁士龙骑', type: 'cavalry', cost: 4, atk: 4, hp: 3, kw: '冲锋' },
    { name: '步兵炮组', type: 'artillery', cost: 3, atk: 2, hp: 3, kw: '远程' },
    { name: '普鲁士重炮', type: 'artillery', cost: 5, atk: 5, hp: 3, kw: '远程' },
    { name: '普鲁士重炮', type: 'artillery', cost: 5, atk: 5, hp: 3, kw: '远程' },
    { name: '黑色布伦瑞克', type: 'infantry', cost: 5, atk: 5, hp: 4, kw: '结阵、突破、死神威慑' },
    { name: '黑色布伦瑞克', type: 'infantry', cost: 5, atk: 5, hp: 4, kw: '结阵、突破、死神威慑' },
    { name: '布吕歇尔的近卫', type: 'guard', cost: 6, atk: 6, hp: 6, kw: '结阵、守卫' },
    { name: '布吕歇尔的近卫', type: 'guard', cost: 6, atk: 6, hp: 6, kw: '结阵、守卫' },
    { name: '国防动员', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'buff_target_INF+1+2' },
    { name: '国防动员', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'buff_target_INF+1+2' },
    { name: '沙恩霍斯特改革', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'draw1_buff_target_INF+1+1' },
    { name: '布吕歇尔的追击令', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'buff_all_friendly_CAV_GUARD+1' },
    { name: '莱比锡泥泞', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'weather_mud_cavalry-1' },
  ],
  russia: [
    { name: '哥萨克轻骑', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、侧翼迂回、熔岩战术' },
    { name: '哥萨克轻骑', type: 'cavalry', cost: 2, atk: 2, hp: 2, kw: '冲锋、侧翼迂回、熔岩战术' },
    { name: '俄军猎兵团', type: 'skirmisher', cost: 1, atk: 1, hp: 2, kw: '闪避' },
    { name: '俄军猎兵团', type: 'skirmisher', cost: 1, atk: 1, hp: 2, kw: '闪避' },
    { name: '东正教民兵', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵、焦土补给' },
    { name: '东正教民兵', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵、焦土补给' },
    { name: '东正教民兵', type: 'infantry', cost: 2, atk: 2, hp: 3, kw: '结阵、焦土补给' },
    { name: '俄国线列军', type: 'infantry', cost: 3, atk: 2, hp: 5, kw: '结阵' },
    { name: '俄国线列军', type: 'infantry', cost: 3, atk: 2, hp: 5, kw: '结阵' },
    { name: '俄国线列军', type: 'infantry', cost: 3, atk: 2, hp: 5, kw: '结阵' },
    { name: '俄国线列军', type: 'infantry', cost: 3, atk: 2, hp: 5, kw: '结阵' },
    { name: '俄军步兵炮', type: 'artillery', cost: 3, atk: 3, hp: 2, kw: '远程' },
    { name: '俄军步兵炮', type: 'artillery', cost: 3, atk: 3, hp: 2, kw: '远程' },
    { name: '西伯利亚老兵', type: 'infantry', cost: 3, atk: 5, hp: 5, kw: '结阵、自残1' },
    { name: '西伯利亚老兵', type: 'infantry', cost: 3, atk: 5, hp: 5, kw: '结阵、自残1' },
    { name: '普拉托夫的哥萨克', type: 'cavalry', cost: 4, atk: 3, hp: 2, kw: '冲锋、侧翼迂回、熔岩战术' },
    { name: '普拉托夫的哥萨克', type: 'cavalry', cost: 4, atk: 3, hp: 2, kw: '冲锋、侧翼迂回、熔岩战术' },
    { name: '俄军龙骑', type: 'cavalry', cost: 4, atk: 4, hp: 3, kw: '冲锋' },
    { name: '俄军龙骑', type: 'cavalry', cost: 4, atk: 4, hp: 3, kw: '冲锋' },
    { name: '莫斯科掷弹兵', type: 'infantry', cost: 5, atk: 4, hp: 5, kw: '结阵、守卫' },
    { name: '莫斯科掷弹兵', type: 'infantry', cost: 5, atk: 4, hp: 5, kw: '结阵、守卫' },
    { name: '独角兽榴弹炮', type: 'artillery', cost: 5, atk: 5, hp: 3, kw: '远程' },
    { name: '独角兽榴弹炮', type: 'artillery', cost: 5, atk: 5, hp: 3, kw: '远程' },
    { name: '巴格拉季昂的近卫', type: 'guard', cost: 6, atk: 5, hp: 6, kw: '结阵、守卫' },
    { name: '巴格拉季昂的近卫', type: 'guard', cost: 6, atk: 5, hp: 6, kw: '结阵、守卫' },
    { name: '库图佐夫的旗手', type: 'guard', cost: 6, atk: 4, hp: 6, kw: '结阵、守卫、自残2、光环+1攻' },
    { name: '帝国大军', type: 'infantry', cost: 5, atk: 3, hp: 5, kw: '结阵、自残1、光环+1血' },
    { name: '库图佐夫的战略后撤', type: 'command', cost: 1, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'retreat_friendly_heal2_hq1' },
    { name: '焦土政策', type: 'command', cost: 2, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'self_hq1_damage_enemy_skirmish1' },
    { name: '冬将军', type: 'command', cost: 3, atk: 0, hp: 0, kw: '事件', kind: 'event', effect: 'weather_winter_all_damage1' },
  ],
  austria: [
    { name: '掷弹兵',     type: 'infantry',   cost: 4, atk: 4, hp: 4, kw: '坚毅' },
    { name: '骠骑兵',     type: 'cavalry',    cost: 4, atk: 4, hp: 3, kw: '冲锋' },
    { name: '边境步兵',   type: 'skirmisher', cost: 2, atk: 2, hp: 3, kw: '散兵' },
    { name: '炮兵连',     type: 'artillery',  cost: 4, atk: 4, hp: 3, kw: '远程' },
    { name: '卡尔大公',   type: 'guard',      cost: 6, atk: 5, hp: 7, kw: '指挥' },
    { name: '胸甲骑兵',   type: 'cavalry',    cost: 5, atk: 5, hp: 4, kw: '冲锋' },
  ],
  spain: [
    { name: '游击队',     type: 'skirmisher', cost: 1, atk: 2, hp: 1, kw: '游击' },
    { name: '步兵团',     type: 'infantry',   cost: 3, atk: 3, hp: 4, kw: '——' },
    { name: '皇家卫队',   type: 'guard',      cost: 5, atk: 4, hp: 5, kw: '坚毅' },
    { name: '龙骑兵',     type: 'cavalry',    cost: 4, atk: 4, hp: 3, kw: '冲锋' },
    { name: '炮兵',       type: 'artillery',  cost: 4, atk: 4, hp: 3, kw: '远程' },
    { name: '埃斯波斯',   type: 'guard',      cost: 6, atk: 5, hp: 6, kw: '游击王' },
  ],
};

window.FACTIONS = FACTIONS;
window.UNIT_TYPES = UNIT_TYPES;
window.FACTION_DECKS = FACTION_DECKS;
