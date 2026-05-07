// Card components — three styles (oil-portrait, heraldry, minimal)
// All accept the same Unit shape: { name, type, cost, atk, hp, kw, faction }

const TYPE_LABEL = {
  infantry: '战列步兵', skirmisher: '散兵', cavalry: '骑兵',
  artillery: '炮兵', guard: '近卫', command: '军令',
};

// ── Style 1: Oil portrait (厚涂笔触, time-period feel) ──────────
function CardOilPortrait({ unit, faction, dead, damaged, scale = 1, onCard = false }) {
  const f = window.FACTIONS[faction];
  const tint = window.UNIT_TYPES[unit.type].tint;
  return (
    <div className="card-oil" style={{
      width: 110 * scale, height: 154 * scale,
      background: `linear-gradient(165deg, #f4ead0 0%, #d8c499 50%, #b89e6f 100%)`,
      border: `2px solid ${f.primary}`,
      borderRadius: 4 * scale,
      padding: 5 * scale,
      display: 'flex', flexDirection: 'column',
      boxShadow: onCard ? `0 ${4*scale}px ${10*scale}px rgba(0,0,0,0.5), inset 0 0 ${20*scale}px rgba(120,80,40,0.35)` : 'none',
      position: 'relative',
      filter: dead ? 'grayscale(0.85) brightness(0.6)' : 'none',
      fontFamily: '"Trajan Pro", "Cinzel", Georgia, serif',
      color: '#2a1f15',
      overflow: 'hidden',
    }}>
      {/* aged paper texture */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        background: `radial-gradient(circle at 30% 20%, transparent 40%, rgba(60,30,10,0.15) 100%),
                     repeating-linear-gradient(45deg, transparent 0, transparent ${3*scale}px, rgba(80,40,20,0.04) ${3*scale}px, rgba(80,40,20,0.04) ${4*scale}px)`,
      }} />
      {/* cost gem */}
      <div style={{
        position: 'absolute', top: -6*scale, left: -6*scale,
        width: 26*scale, height: 26*scale,
        background: `radial-gradient(circle at 35% 30%, #f5d889, #b8862e 70%, #5a3a14)`,
        border: `2px solid #2a1f15`,
        borderRadius: '50%',
        textAlign: 'center', lineHeight: `${22*scale}px`,
        fontWeight: 'bold', fontSize: 14*scale, color: '#2a1f15',
        boxShadow: `0 ${2*scale}px ${4*scale}px rgba(0,0,0,0.6)`,
        zIndex: 2,
      }}>{unit.cost}</div>
      {/* portrait area (placeholder: painted bust silhouette) */}
      <div style={{
        height: 70*scale, position: 'relative', overflow: 'hidden',
        border: `1px solid ${f.primary}`,
        background: `radial-gradient(ellipse at 50% 30%, ${tint} 0%, ${f.primary}88 60%, #1a1410 100%)`,
        marginBottom: 3*scale,
      }}>
        {/* painted silhouette */}
        <svg viewBox="0 0 100 70" preserveAspectRatio="xMidYMid slice" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
          <defs>
            <radialGradient id={`p-${unit.name}-${faction}`} cx="0.5" cy="0.4">
              <stop offset="0" stopColor="#f4ead0" stopOpacity="0.4"/>
              <stop offset="1" stopColor="#1a0a04" stopOpacity="0.7"/>
            </radialGradient>
          </defs>
          {/* atmospheric backdrop */}
          <rect width="100" height="70" fill={`url(#p-${unit.name}-${faction})`}/>
          {/* distant cannon smoke */}
          <ellipse cx="20" cy="55" rx="25" ry="6" fill="rgba(80,60,40,0.4)"/>
          <ellipse cx="80" cy="58" rx="20" ry="5" fill="rgba(60,40,20,0.5)"/>
          {/* figure silhouette varies by type */}
          {unit.type === 'cavalry' && (
            <g transform="translate(50,42)" fill="#1a0a04">
              <ellipse cx="0" cy="8" rx="22" ry="6"/>
              <path d="M-15,-2 Q-10,-12 -2,-10 L8,-8 Q18,-6 18,4 L18,8 L-15,8 Z"/>
              <circle cx="-8" cy="-14" r="5"/>
              <path d="M-5,-19 L-3,-22 L-1,-19 Z" fill={f.accent}/>
            </g>
          )}
          {unit.type === 'infantry' && (
            <g transform="translate(50,38)" fill="#1a0a04">
              <path d="M-5,-15 Q-5,-22 0,-22 Q5,-22 5,-15 L5,-10 L-5,-10 Z"/>
              <rect x="-9" y="-10" width="18" height="22" rx="2"/>
              <path d="M-12,-8 L-9,-8 L-9,12 L-12,12 Z M9,-8 L12,-8 L12,12 L9,12 Z"/>
              {/* shako plume */}
              <path d="M-2,-22 L0,-28 L2,-22 Z" fill={f.accent}/>
              {/* musket */}
              <line x1="10" y1="-8" x2="14" y2="-22" stroke="#3a2818" strokeWidth="1.2"/>
            </g>
          )}
          {unit.type === 'artillery' && (
            <g transform="translate(50,46)" fill="#1a0a04">
              <rect x="-22" y="-2" width="40" height="6" rx="1"/>
              <circle cx="-14" cy="6" r="6" fill="#2a1f15"/>
              <circle cx="14" cy="6" r="6" fill="#2a1f15"/>
              <rect x="-4" y="-10" width="22" height="6" transform="rotate(-8)"/>
              {/* muzzle flash */}
              <circle cx="20" cy="-8" r="3" fill="#f5d889" opacity="0.8"/>
            </g>
          )}
          {unit.type === 'skirmisher' && (
            <g transform="translate(50,40)" fill="#1a0a04">
              <circle cx="0" cy="-15" r="4"/>
              <path d="M-4,-11 L4,-11 L6,8 L-6,8 Z"/>
              <line x1="6" y1="-5" x2="14" y2="-12" stroke="#3a2818" strokeWidth="1.2"/>
              <line x1="-12" y1="0" x2="-6" y2="-3" stroke="#3a2818" strokeWidth="0.8"/>
            </g>
          )}
          {unit.type === 'guard' && (
            <g transform="translate(50,36)" fill="#1a0a04">
              <path d="M-7,-20 Q-7,-26 0,-26 Q7,-26 7,-20 L7,-12 L-7,-12 Z"/>
              <rect x="-10" y="-12" width="20" height="24" rx="2"/>
              {/* bearskin hat */}
              <ellipse cx="0" cy="-26" rx="9" ry="8" fill="#1a0a04"/>
              <ellipse cx="0" cy="-30" rx="7" ry="3" fill="#1a0a04"/>
              {/* gold trim */}
              <rect x="-10" y="-8" width="20" height="2" fill={f.gold}/>
              <line x1="0" y1="-12" x2="0" y2="12" stroke={f.gold} strokeWidth="0.8"/>
            </g>
          )}
        </svg>
        {/* heavy painterly vignette */}
        <div style={{
          position: 'absolute', inset: 0,
          background: `radial-gradient(ellipse at 50% 40%, transparent 30%, rgba(20,10,4,0.7) 100%)`,
        }}/>
      </div>
      {/* name plate */}
      <div style={{
        fontSize: 11*scale, fontWeight: 'bold', textAlign: 'center',
        letterSpacing: scale > 0.7 ? '0.5px' : '0',
        lineHeight: 1.15, height: 26*scale, overflow: 'hidden',
        background: `linear-gradient(to right, transparent, rgba(212,165,92,0.3), transparent)`,
        borderTop: `1px solid ${f.gold}`,
        borderBottom: `1px solid ${f.gold}`,
        padding: `${3*scale}px 0`,
        color: '#1a1006',
        textShadow: '0 1px 0 rgba(255,240,200,0.3)',
      }}>{unit.name}</div>
      {/* keywords */}
      <div style={{
        flex: 1, fontSize: 9*scale, textAlign: 'center',
        color: f.primary, fontStyle: 'italic',
        padding: `${3*scale}px 0`, fontFamily: 'Georgia, serif',
      }}>{unit.kw}</div>
      {/* stats */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', padding: `${2*scale}px ${4*scale}px`,
      }}>
        <div style={{
          width: 22*scale, height: 22*scale,
          background: `radial-gradient(circle at 30% 30%, #d6755a, #8b3a1f 70%, #4a1505)`,
          border: '1.5px solid #2a1f15', borderRadius: '50%',
          color: '#fff', fontWeight: 'bold', fontSize: 13*scale,
          textAlign: 'center', lineHeight: `${19*scale}px`,
          boxShadow: `inset 0 -${1*scale}px ${2*scale}px rgba(0,0,0,0.4)`,
        }}>{unit.atk}</div>
        <div style={{fontSize: 9*scale, color: '#5a4530', letterSpacing: '1px'}}>
          {window.UNIT_TYPES[unit.type].icon}
        </div>
        <div style={{
          width: 22*scale, height: 22*scale,
          background: `radial-gradient(circle at 30% 30%, ${damaged ? '#e88860' : '#7fa56f'}, ${damaged ? '#a83014' : '#2d5a3d'} 70%, #1a3020)`,
          border: '1.5px solid #2a1f15', borderRadius: '50%',
          color: '#fff', fontWeight: 'bold', fontSize: 13*scale,
          textAlign: 'center', lineHeight: `${19*scale}px`,
          boxShadow: `inset 0 -${1*scale}px ${2*scale}px rgba(0,0,0,0.4)`,
        }}>{unit.hp}</div>
      </div>
    </div>
  );
}

// ── Style 2: Heraldry (纹章风, 装饰性) ───────────────────────
function CardHeraldry({ unit, faction, dead, damaged, scale = 1, onCard = false }) {
  const f = window.FACTIONS[faction];
  const t = window.UNIT_TYPES[unit.type];
  return (
    <div style={{
      width: 110*scale, height: 154*scale,
      background: `linear-gradient(180deg, ${f.primary} 0%, #1a1410 100%)`,
      border: `${2*scale}px solid ${f.gold}`,
      borderRadius: 4*scale,
      position: 'relative',
      boxShadow: onCard ? `0 ${4*scale}px ${10*scale}px rgba(0,0,0,0.5)` : 'none',
      filter: dead ? 'grayscale(0.85) brightness(0.6)' : 'none',
      fontFamily: 'Georgia, serif',
      overflow: 'hidden',
    }}>
      {/* damask pattern */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `radial-gradient(circle at 50% 50%, ${f.gold}22 1px, transparent 2px)`,
        backgroundSize: `${10*scale}px ${10*scale}px`,
      }}/>
      {/* corner flourishes */}
      <svg viewBox="0 0 110 154" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
        <g fill="none" stroke={f.gold} strokeWidth="0.6">
          <path d="M3,3 L20,3 M3,3 L3,20 M3,15 Q10,15 15,3"/>
          <path d="M107,3 L90,3 M107,3 L107,20 M107,15 Q100,15 95,3"/>
          <path d="M3,151 L20,151 M3,151 L3,134 M3,139 Q10,139 15,151"/>
          <path d="M107,151 L90,151 M107,151 L107,134 M107,139 Q100,139 95,151"/>
        </g>
      </svg>
      {/* cost */}
      <div style={{
        position: 'absolute', top: -6*scale, left: -6*scale,
        width: 26*scale, height: 26*scale,
        background: `radial-gradient(circle at 35% 30%, ${f.gold}, ${f.accent})`,
        border: `${2*scale}px solid ${f.primary}`,
        borderRadius: '50%',
        textAlign: 'center', lineHeight: `${22*scale}px`,
        fontWeight: 'bold', fontSize: 14*scale, color: f.primary,
        zIndex: 2,
      }}>{unit.cost}</div>
      {/* central crest area */}
      <div style={{position: 'absolute', top: 14*scale, left: 0, right: 0, textAlign: 'center'}}>
        <div dangerouslySetInnerHTML={{__html: f.crest(70*scale)}}/>
      </div>
      {/* type icon over crest */}
      <div style={{
        position: 'absolute', top: 50*scale, left: 0, right: 0,
        textAlign: 'center', fontSize: 24*scale, color: f.gold,
        textShadow: `0 ${2*scale}px ${4*scale}px rgba(0,0,0,0.8)`,
      }}>{t.icon}</div>
      {/* name banner */}
      <div style={{
        position: 'absolute', top: 92*scale, left: 4*scale, right: 4*scale,
        background: `linear-gradient(to right, transparent, ${f.gold}cc, transparent)`,
        textAlign: 'center', fontSize: 10*scale, fontWeight: 'bold',
        color: f.primary, padding: `${3*scale}px ${4*scale}px`,
        lineHeight: 1.1,
        textShadow: `0 ${1*scale}px 0 ${f.gold}66`,
      }}>{unit.name}</div>
      {/* type label */}
      <div style={{
        position: 'absolute', top: 116*scale, left: 0, right: 0,
        textAlign: 'center', fontSize: 9*scale,
        color: f.gold, fontStyle: 'italic',
        letterSpacing: scale > 0.7 ? '1px' : 0,
      }}>{t.name}</div>
      {/* stats */}
      <div style={{
        position: 'absolute', bottom: 4*scale, left: 6*scale, right: 6*scale,
        display: 'flex', justifyContent: 'space-between',
      }}>
        <div style={{
          width: 24*scale, height: 24*scale,
          background: `linear-gradient(135deg, #d6755a, #8b3a1f)`,
          border: `${1.5*scale}px solid ${f.gold}`,
          borderRadius: 3*scale,
          color: '#fff', fontWeight: 'bold', fontSize: 13*scale,
          textAlign: 'center', lineHeight: `${21*scale}px`,
        }}>{unit.atk}</div>
        <div style={{
          width: 24*scale, height: 24*scale,
          background: `linear-gradient(135deg, ${damaged ? '#e88860' : '#7fa56f'}, ${damaged ? '#a83014' : '#2d5a3d'})`,
          border: `${1.5*scale}px solid ${f.gold}`,
          borderRadius: 3*scale,
          color: '#fff', fontWeight: 'bold', fontSize: 13*scale,
          textAlign: 'center', lineHeight: `${21*scale}px`,
        }}>{unit.hp}</div>
      </div>
    </div>
  );
}

// ── Style 3: Minimal (现代极简) ──────────────────────────────
function CardMinimal({ unit, faction, dead, damaged, scale = 1, onCard = false }) {
  const f = window.FACTIONS[faction];
  const t = window.UNIT_TYPES[unit.type];
  return (
    <div style={{
      width: 110*scale, height: 154*scale,
      background: '#f4f0e8',
      border: `${1.5*scale}px solid #1a1410`,
      borderTop: `${10*scale}px solid ${f.primary}`,
      borderRadius: 2*scale,
      position: 'relative',
      boxShadow: onCard ? `${3*scale}px ${4*scale}px 0 #1a1410` : 'none',
      filter: dead ? 'grayscale(0.85) brightness(0.7)' : 'none',
      fontFamily: '"Helvetica Neue", Arial, sans-serif',
      color: '#1a1410',
      padding: 6*scale,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
        <div style={{
          fontSize: 18*scale, fontWeight: 900, lineHeight: 1,
          color: f.primary,
        }}>{unit.cost}</div>
        <div style={{fontSize: 16*scale, color: f.primary}}>{t.icon}</div>
      </div>
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', textAlign: 'center', padding: `${4*scale}px 0`}}>
        <div style={{fontSize: 11*scale, fontWeight: 800, lineHeight: 1.15, marginBottom: 4*scale}}>{unit.name}</div>
        <div style={{
          fontSize: 8*scale, textTransform: 'uppercase',
          letterSpacing: scale > 0.7 ? '2px' : '0.5px',
          color: '#8b6f47',
        }}>{t.name}</div>
      </div>
      <div style={{
        fontSize: 8*scale, textAlign: 'center',
        color: f.primary, fontWeight: 600,
        borderTop: `1px solid ${f.primary}33`,
        paddingTop: 3*scale, marginBottom: 3*scale,
      }}>{unit.kw}</div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: 16*scale, fontWeight: 900,
      }}>
        <span style={{color: '#8b3a1f'}}>{unit.atk}</span>
        <span style={{color: damaged ? '#c2552c' : '#2d5a3d'}}>{unit.hp}</span>
      </div>
    </div>
  );
}

// dispatcher
function Card({ style, ...props }) {
  if (style === 'heraldry') return <CardHeraldry {...props}/>;
  if (style === 'minimal') return <CardMinimal {...props}/>;
  return <CardOilPortrait {...props}/>;
}

window.Card = Card;
window.TYPE_LABEL = TYPE_LABEL;
