// Battlefield component — drag to deploy, attack animations, particles, screen shake
// Layout: P2 rear (top) → P2 front → shared skirmish (middle) → P1 front → P1 rear (bottom)
// All interactions live here. Visual variants come from the `theme` prop.

const { useState, useEffect, useRef, useCallback } = React;

const INITIAL_MORALE = 1;
const MAX_MORALE = 10;

// ─────────── Action Queue ───────────
function useActionQueue() {
  const [locked, setLocked] = useState(false);
  const pendingRef = useRef(null);

  const tryRun = useCallback((fn) => {
    if (locked) {
      pendingRef.current = fn;
      return false;
    }
    setLocked(true);
    fn(() => {
      setLocked(false);
      const next = pendingRef.current;
      pendingRef.current = null;
      if (next) tryRun(next);
    });
    return true;
  }, [locked]);

  return { locked, tryRun };
}

// ─────────── Background renderers ───────────
// Painted battlefield scene with torn flags, broken sabers, fallen soldiers,
// muddy puddles, scattered cannonballs, firing artillery, distant beacons.
function BattlefieldBg({ kind, mood }) {
  const moodPalette = {
    warm:   { sky1: '#5a3520', sky2: '#3a2010', sky3: '#1a0e08', sun: '#f5b568', smoke: '#6a4a30', mud: '#3a2818', accent: '#d4a55c' },
    cold:   { sky1: '#2a3a5a', sky2: '#1a2438', sky3: '#080d18', sun: '#a8c0e0', smoke: '#4a5870', mud: '#1a2030', accent: '#7fa5d4' },
    dusk:   { sky1: '#7a3818', sky2: '#3a1810', sky3: '#0a0604', sun: '#f5803c', smoke: '#5a3020', mud: '#2a1610', accent: '#e8a050' },
    night:  { sky1: '#1a2030', sky2: '#0a1020', sky3: '#000408', sun: '#c0d0e8', smoke: '#3a4050', mud: '#0a1018', accent: '#a0b8d4' },
  }[mood] || { sky1: '#2a3a5a', sky2: '#1a2438', sky3: '#080d18', sun: '#a8c0e0', smoke: '#4a5870', mud: '#1a2030', accent: '#7fa5d4' };

  if (kind === 'sandtable') {
    return <SandtableBg/>;
  }
  if (kind === 'map') {
    return <MapBg/>;
  }
  // Default: painted battlefield
  return <PaintedBattlefield p={moodPalette}/>;
}

// ─────────── Painted battlefield (the main one) ───────────
function PaintedBattlefield({ p }) {
  return (
    <div style={{position: 'absolute', inset: 0, borderRadius: 6, overflow: 'hidden'}}>
      <svg viewBox="0 0 1280 780" preserveAspectRatio="xMidYMid slice"
           style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
        <defs>
          {/* sky / atmospheric gradient */}
          <linearGradient id="bf-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={p.sky1}/>
            <stop offset="0.35" stopColor={p.sky2}/>
            <stop offset="0.55" stopColor={p.sky3}/>
            <stop offset="1" stopColor={p.mud}/>
          </linearGradient>
          {/* dying sun / beacon */}
          <radialGradient id="bf-sun" cx="0.78" cy="0.22" r="0.4">
            <stop offset="0" stopColor={p.sun} stopOpacity="0.95"/>
            <stop offset="0.15" stopColor={p.sun} stopOpacity="0.55"/>
            <stop offset="0.5" stopColor={p.accent} stopOpacity="0.15"/>
            <stop offset="1" stopColor="transparent"/>
          </radialGradient>
          {/* smoke billows */}
          <radialGradient id="bf-smoke" cx="0.5" cy="0.5">
            <stop offset="0" stopColor={p.smoke} stopOpacity="0.8"/>
            <stop offset="1" stopColor={p.smoke} stopOpacity="0"/>
          </radialGradient>
          {/* muzzle flash */}
          <radialGradient id="bf-flash">
            <stop offset="0" stopColor="#fff5c0" stopOpacity="1"/>
            <stop offset="0.4" stopColor="#f5b040" stopOpacity="0.7"/>
            <stop offset="1" stopColor="transparent"/>
          </radialGradient>
          {/* mud puddle */}
          <radialGradient id="bf-puddle">
            <stop offset="0" stopColor={p.sky2} stopOpacity="0.6"/>
            <stop offset="1" stopColor={p.mud} stopOpacity="1"/>
          </radialGradient>
          {/* darkening vignette over center where game is played */}
          <radialGradient id="bf-vignette" cx="0.5" cy="0.5" r="0.7">
            <stop offset="0" stopColor="#000" stopOpacity="0.55"/>
            <stop offset="0.6" stopColor="#000" stopOpacity="0.7"/>
            <stop offset="1" stopColor="#000" stopOpacity="0.85"/>
          </radialGradient>
        </defs>

        {/* SKY */}
        <rect width="1280" height="780" fill="url(#bf-sky)"/>
        <rect width="1280" height="780" fill="url(#bf-sun)"/>

        {/* distant beacons / fires on the horizon */}
        <g opacity="0.85">
          <ellipse cx="180" cy="290" rx="35" ry="6" fill="#f58030" opacity="0.35"/>
          <ellipse cx="180" cy="285" rx="14" ry="20" fill="#f5a040" opacity="0.45"/>
          <ellipse cx="180" cy="278" rx="8" ry="14" fill="#fff0a0" opacity="0.6"/>
          <ellipse cx="450" cy="295" rx="40" ry="8" fill="#e08020" opacity="0.3"/>
          <ellipse cx="450" cy="288" rx="18" ry="22" fill="#f08030" opacity="0.4"/>
          <ellipse cx="900" cy="280" rx="50" ry="8" fill="#d06020" opacity="0.35"/>
          <ellipse cx="900" cy="272" rx="20" ry="25" fill="#f08030" opacity="0.45"/>
          <ellipse cx="900" cy="264" rx="10" ry="16" fill="#fff080" opacity="0.6"/>
          {/* black smoke columns rising */}
          <ellipse cx="180" cy="200" rx="40" ry="60" fill={p.sky3} opacity="0.5"/>
          <ellipse cx="450" cy="180" rx="55" ry="80" fill={p.sky3} opacity="0.45"/>
          <ellipse cx="900" cy="160" rx="65" ry="90" fill={p.sky3} opacity="0.55"/>
          <ellipse cx="1100" cy="220" rx="45" ry="70" fill={p.sky3} opacity="0.4"/>
        </g>

        {/* distant ridgeline w/ tiny silhouettes */}
        <path d="M0,330 Q160,310 280,325 Q420,340 560,318 Q720,305 880,322 Q1050,335 1280,315 L1280,360 L0,360 Z"
              fill={p.sky3} opacity="0.7"/>
        {/* small marching column silhouettes */}
        <g fill="#000" opacity="0.55">
          {Array.from({length: 14}).map((_, i) => (
            <rect key={i} x={140 + i*18} y={325 - (i%2)} width="1.2" height="5"/>
          ))}
          {Array.from({length: 10}).map((_, i) => (
            <rect key={'b'+i} x={620 + i*16} y={320 - (i%2)} width="1.2" height="5"/>
          ))}
        </g>

        {/* mid-ground smoke billows */}
        <g>
          <ellipse cx="300" cy="380" rx="160" ry="40" fill="url(#bf-smoke)" opacity="0.7"/>
          <ellipse cx="640" cy="370" rx="220" ry="55" fill="url(#bf-smoke)" opacity="0.65"/>
          <ellipse cx="1000" cy="385" rx="180" ry="45" fill="url(#bf-smoke)" opacity="0.7"/>
        </g>

        {/* mid-ground hills */}
        <path d="M0,400 Q200,380 400,398 Q600,415 800,395 Q1000,378 1280,402 L1280,440 L0,440 Z"
              fill={p.mud} opacity="0.9"/>

        {/* cannons firing on the right side, distant */}
        <g transform="translate(1080, 425)">
          {/* cannon body */}
          <rect x="-30" y="-4" width="50" height="8" fill="#1a1410"/>
          <rect x="-32" y="-6" width="6" height="12" fill="#3a2818"/>
          {/* wheels */}
          <circle cx="-20" cy="6" r="9" fill="#1a0e08"/>
          <circle cx="-20" cy="6" r="9" fill="none" stroke="#3a2818" strokeWidth="0.6"/>
          <circle cx="0" cy="6" r="9" fill="#1a0e08"/>
          {/* muzzle flash */}
          <ellipse cx="28" cy="0" rx="22" ry="10" fill="url(#bf-flash)" opacity="0.95"/>
          <circle cx="20" cy="0" r="6" fill="#fff5c0"/>
        </g>
        <g transform="translate(140, 430)" transform-origin="center">
          <rect x="-2" y="-4" width="50" height="8" fill="#1a1410"/>
          <rect x="44" y="-6" width="6" height="12" fill="#3a2818"/>
          <circle cx="35" cy="6" r="9" fill="#1a0e08"/>
          <circle cx="15" cy="6" r="9" fill="#1a0e08"/>
          <ellipse cx="-10" cy="0" rx="20" ry="9" fill="url(#bf-flash)" opacity="0.85"/>
        </g>

        {/* FOREGROUND EARTH — dark mud */}
        <path d="M0,440 L1280,440 L1280,780 L0,780 Z" fill={p.mud}/>
        {/* irregular dirt mounds */}
        <path d="M0,440 Q60,448 130,442 Q200,436 280,448 Q360,460 440,442 Q520,438 600,452 Q680,460 760,444 Q850,438 930,452 Q1010,460 1100,442 Q1180,438 1280,448 L1280,470 L0,470 Z"
              fill="#000" opacity="0.4"/>

        {/* mud puddles scattered */}
        <ellipse cx="220" cy="540" rx="55" ry="10" fill="url(#bf-puddle)" opacity="0.7"/>
        <ellipse cx="700" cy="600" rx="80" ry="14" fill="url(#bf-puddle)" opacity="0.6"/>
        <ellipse cx="1050" cy="560" rx="50" ry="9" fill="url(#bf-puddle)" opacity="0.7"/>
        <ellipse cx="380" cy="680" rx="70" ry="12" fill="url(#bf-puddle)" opacity="0.65"/>
        <ellipse cx="980" cy="710" rx="60" ry="10" fill="url(#bf-puddle)" opacity="0.6"/>

        {/* scattered cannonballs */}
        <g fill="#0a0604">
          <circle cx="160" cy="620" r="6"/><circle cx="175" cy="625" r="5"/>
          <circle cx="540" cy="700" r="7"/><circle cx="555" cy="708" r="6"/><circle cx="525" cy="710" r="5"/>
          <circle cx="820" cy="640" r="6"/>
          <circle cx="1140" cy="690" r="7"/><circle cx="1155" cy="697" r="5"/>
          <circle cx="60" cy="710" r="6"/>
          {/* highlights */}
          <circle cx="158" cy="618" r="1.5" fill={p.accent} opacity="0.4"/>
          <circle cx="538" cy="697" r="1.8" fill={p.accent} opacity="0.4"/>
          <circle cx="818" cy="638" r="1.5" fill={p.accent} opacity="0.4"/>
          <circle cx="1138" cy="687" r="1.8" fill={p.accent} opacity="0.4"/>
        </g>

        {/* broken artillery wheel — left foreground */}
        <g transform="translate(80,640) rotate(-20)">
          <circle cx="0" cy="0" r="34" fill="none" stroke="#2a1610" strokeWidth="4"/>
          <circle cx="0" cy="0" r="6" fill="#2a1610"/>
          {[0, 45, 90, 135, 180, 225, 270, 315].map((a, i) => (
            <line key={i} x1="0" y1="0" x2={Math.cos(a*Math.PI/180)*32} y2={Math.sin(a*Math.PI/180)*32}
                  stroke="#2a1610" strokeWidth="3"/>
          ))}
          {/* broken spoke */}
          <line x1="0" y1="0" x2="14" y2="-8" stroke="#2a1610" strokeWidth="3"/>
        </g>

        {/* broken sabre — right foreground */}
        <g transform="translate(1100, 700) rotate(35)">
          <rect x="-2" y="-50" width="4" height="50" fill="#5a5550" opacity="0.85"/>
          <rect x="-3" y="-60" width="6" height="12" fill="#3a2818"/>
          <path d="M-5,-58 Q-12,-50 -5,-46" fill="none" stroke="#8b6f1e" strokeWidth="2"/>
          {/* broken tip lying nearby */}
          <g transform="translate(20,-5) rotate(-50)">
            <rect x="-1.5" y="-22" width="3" height="22" fill="#5a5550" opacity="0.85"/>
          </g>
        </g>

        {/* torn regimental flag — left mid */}
        <g transform="translate(280, 580)">
          {/* flagpole, broken */}
          <line x1="0" y1="20" x2="-8" y2="-90" stroke="#3a2818" strokeWidth="3"/>
          {/* gold finial (eagle) */}
          <g transform="translate(-9,-92)">
            <path d="M-4,0 L0,-8 L4,0 L2,2 L-2,2 Z" fill={p.accent}/>
            <circle cx="0" cy="-3" r="1.5" fill={p.accent}/>
          </g>
          {/* tattered cloth */}
          <path d="M-7,-85 L48,-78 L52,-65 L42,-48 L48,-32 L36,-20 L20,-30 L8,-20 L-5,-25 L-7,-85 Z"
                fill="#8b1a1a" opacity="0.85"/>
          <path d="M-7,-85 L48,-78 L52,-65 L42,-48 L48,-32 L36,-20 L20,-30 L8,-20 L-5,-25 L-7,-85 Z"
                fill="none" stroke="#3a0808" strokeWidth="0.8" opacity="0.6"/>
          {/* embroidered N or eagle */}
          <text x="22" y="-50" fontSize="14" fill={p.accent} fontFamily="serif" fontWeight="bold" opacity="0.7">N</text>
          {/* tear edges */}
          <path d="M48,-32 L54,-28 L50,-24 L48,-32 M36,-20 L32,-14 L28,-18" fill="#3a0808" opacity="0.7"/>
        </g>

        {/* second torn flag — right mid */}
        <g transform="translate(940, 600) scale(-1, 1)">
          <line x1="0" y1="20" x2="-6" y2="-80" stroke="#3a2818" strokeWidth="3"/>
          <path d="M-6,-78 L40,-72 L44,-58 L36,-44 L42,-30 L28,-22 L14,-30 L0,-22 L-4,-26 L-6,-78 Z"
                fill="#1e3a6f" opacity="0.85"/>
          <path d="M-6,-78 L40,-72 L44,-58 L36,-44 L42,-30 L28,-22 L14,-30 L0,-22 L-4,-26 L-6,-78 Z"
                fill="none" stroke="#0a1428" strokeWidth="0.8" opacity="0.6"/>
        </g>

        {/* fallen soldier — right foreground */}
        <g transform="translate(820, 700)">
          {/* body lying */}
          <ellipse cx="0" cy="0" rx="35" ry="9" fill="#1a0e08"/>
          <ellipse cx="-25" cy="-2" rx="10" ry="8" fill="#1a0e08"/>
          {/* shako fallen off */}
          <ellipse cx="-40" cy="2" rx="8" ry="5" fill="#0a0604"/>
          <rect x="-44" y="0" width="8" height="3" fill={p.accent} opacity="0.4"/>
          {/* musket beside */}
          <line x1="10" y1="-2" x2="40" y2="-12" stroke="#3a2818" strokeWidth="2.5"/>
          <line x1="10" y1="-2" x2="40" y2="-12" stroke="#5a4530" strokeWidth="0.8"/>
        </g>

        {/* second fallen soldier — left foreground */}
        <g transform="translate(420, 730) rotate(8)">
          <ellipse cx="0" cy="0" rx="32" ry="8" fill="#1a0e08"/>
          <ellipse cx="22" cy="-2" rx="9" ry="7" fill="#1a0e08"/>
          {/* arm out */}
          <ellipse cx="-15" cy="6" rx="14" ry="4" fill="#1a0e08"/>
          {/* hat */}
          <ellipse cx="35" cy="-4" rx="8" ry="6" fill="#0a0604"/>
        </g>

        {/* third fallen soldier — center mid */}
        <g transform="translate(640, 660) rotate(-15)">
          <ellipse cx="0" cy="0" rx="28" ry="7" fill="#1a0e08"/>
          <ellipse cx="-22" cy="-1" rx="8" ry="6" fill="#1a0e08"/>
          {/* sabre out */}
          <line x1="20" y1="0" x2="48" y2="-8" stroke="#5a5550" strokeWidth="2"/>
        </g>

        {/* drum, broken — far right */}
        <g transform="translate(1180, 720) rotate(20)">
          <ellipse cx="0" cy="6" rx="22" ry="5" fill="#1a0e08" opacity="0.5"/>
          <rect x="-22" y="-12" width="44" height="22" rx="3" fill="#8b3a1f"/>
          <rect x="-22" y="-12" width="44" height="3" fill="#3a1808"/>
          <rect x="-22" y="7" width="44" height="3" fill="#3a1808"/>
          {/* zigzag pattern */}
          <path d="M-20,-2 L-12,-8 L-4,-2 L4,-8 L12,-2 L20,-8" fill="none" stroke={p.accent} strokeWidth="0.8" opacity="0.6"/>
          {/* hole punched through */}
          <ellipse cx="3" cy="-1" rx="7" ry="5" fill="#0a0604"/>
        </g>

        {/* abandoned bayonet stuck in mud */}
        <g transform="translate(560, 620) rotate(-25)">
          <line x1="0" y1="0" x2="0" y2="-32" stroke="#7a7570" strokeWidth="2"/>
          <line x1="0" y1="0" x2="0" y2="-32" stroke="#bcb6a8" strokeWidth="0.6"/>
          <rect x="-1" y="-2" width="2" height="6" fill="#3a2818"/>
        </g>

        {/* low-lying battle smoke drifting across the play area */}
        <g opacity="0.35">
          <ellipse cx="200" cy="500" rx="120" ry="20" fill={p.smoke}/>
          <ellipse cx="500" cy="490" rx="180" ry="25" fill={p.smoke}/>
          <ellipse cx="900" cy="510" rx="160" ry="22" fill={p.smoke}/>
        </g>

        {/* large vignette to keep card area readable */}
        <rect width="1280" height="780" fill="url(#bf-vignette)" opacity="0.55"/>
      </svg>
    </div>
  );
}

// ─────────── Sandtable bg ───────────
function SandtableBg() {
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 6}}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `repeating-linear-gradient(90deg, #3a2010 0, #4a2818 8px, #3a2010 16px)`,
      }}/>
      <div style={{
        position: 'absolute', inset: 14,
        background: `radial-gradient(ellipse at 50% 50%, #c9a973 0%, #8a6a3a 70%, #5a3a1c 100%)`,
        boxShadow: 'inset 0 0 80px rgba(0,0,0,0.6)',
      }}>
        <svg viewBox="0 0 1280 780" preserveAspectRatio="xMidYMid slice" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
          {/* contour ridges */}
          <g fill="none" stroke="#5a3a1c" strokeWidth="1.5" opacity="0.4">
            <path d="M0,200 Q300,180 600,210 T1280,200"/>
            <path d="M0,400 Q400,370 700,420 T1280,400"/>
            <path d="M0,580 Q280,560 540,600 T1280,580"/>
          </g>
          {/* river */}
          <path d="M-50,280 Q280,320 540,300 Q800,280 1280,340" fill="none" stroke="#5a8aa8" strokeWidth="6" opacity="0.45"/>
          {/* miniature trees */}
          {Array.from({length: 24}).map((_, i) => (
            <g key={i} transform={`translate(${100 + (i*47)%1100},${150 + ((i*13)%500)})`}>
              <circle cx="0" cy="0" r="6" fill="#3a5028"/>
              <rect x="-1" y="0" width="2" height="6" fill="#3a2818"/>
            </g>
          ))}
          {/* miniature buildings */}
          <g fill="#7a5530" stroke="#3a2010" strokeWidth="0.8">
            <rect x="200" y="350" width="22" height="16"/><polygon points="200,350 211,344 222,350" fill="#3a2010"/>
            <rect x="900" y="220" width="22" height="16"/><polygon points="900,220 911,214 922,220" fill="#3a2010"/>
            <rect x="600" y="500" width="28" height="20"/><polygon points="600,500 614,492 628,500" fill="#3a2010"/>
          </g>
          {/* tin soldiers — rows of red & blue dots */}
          <g>
            {Array.from({length: 16}).map((_, i) => <circle key={'r'+i} cx={300 + i*30} cy="180" r="3" fill="#8b1a1a"/>)}
            {Array.from({length: 16}).map((_, i) => <circle key={'b'+i} cx={300 + i*30} cy="600" r="3" fill="#1e3a6f"/>)}
          </g>
          {/* compass and flags */}
          <g transform="translate(1180, 80)">
            <circle r="20" fill="#f4e4c1" stroke="#5a3a1c" strokeWidth="1"/>
            <path d="M0,-15 L3,0 L0,15 L-3,0 Z" fill="#8b1a1a"/>
            <text y="-22" textAnchor="middle" fontSize="10" fill="#3a2010" fontFamily="serif">N</text>
          </g>
        </svg>
      </div>
    </div>
  );
}

// ─────────── Map bg ───────────
function MapBg() {
  return (
    <div style={{
      position: 'absolute', inset: 0, borderRadius: 6, overflow: 'hidden',
      background: `linear-gradient(180deg, #d8c499 0%, #b89a6a 100%)`,
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 30% 20%, transparent 30%, rgba(60,30,10,0.25) 100%),
                     radial-gradient(ellipse at 70% 80%, transparent 30%, rgba(60,30,10,0.3) 100%)`,
      }}/>
      <svg viewBox="0 0 1280 780" preserveAspectRatio="xMidYMid slice" style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}>
        {/* country outlines (Europe simplified) */}
        <g fill="none" stroke="#5a3a1c" strokeWidth="2" opacity="0.55">
          <path d="M60,300 Q180,220 300,260 Q420,310 360,440 Q280,560 380,640 L240,680 Q60,580 60,300 Z"/>
          <path d="M420,120 Q600,80 780,160 Q840,320 720,440 L540,440 Q420,310 420,120 Z"/>
          <path d="M780,80 Q1020,120 1080,320 Q1100,520 960,640 L780,600 Q720,440 780,80 Z"/>
        </g>
        {/* city dots */}
        <g fill="#8b1a1a">
          <circle cx="240" cy="400" r="4"/><text x="248" y="404" fontSize="11" fill="#3a1808" fontFamily="serif">Madrid</text>
          <circle cx="600" cy="280" r="4"/><text x="608" y="284" fontSize="11" fill="#3a1808" fontFamily="serif">Paris</text>
          <circle cx="850" cy="260" r="4"/><text x="858" y="264" fontSize="11" fill="#3a1808" fontFamily="serif">Wien</text>
          <circle cx="780" cy="180" r="4"/><text x="788" y="184" fontSize="11" fill="#3a1808" fontFamily="serif">Berlin</text>
          <circle cx="980" cy="140" r="4"/><text x="988" y="144" fontSize="11" fill="#3a1808" fontFamily="serif">Москва</text>
        </g>
        {/* battle markers (crossed swords) */}
        <g stroke="#8b1a1a" strokeWidth="2.5" opacity="0.85">
          <path d="M280,420 L300,440 M300,420 L280,440"/>
          <path d="M620,300 L640,320 M640,300 L620,320"/>
          <path d="M860,280 L880,300 M880,280 L860,300"/>
        </g>
        {/* compass rose */}
        <g transform="translate(1140,100)" fill="#5a3a1c" opacity="0.6">
          <circle r="30" fill="none" stroke="#5a3a1c" strokeWidth="1.5"/>
          <path d="M0,-25 L4,0 L0,25 L-4,0 Z"/>
          <path d="M-25,0 L0,4 L25,0 L0,-4 Z"/>
          <text y="-32" textAnchor="middle" fontSize="14" fontFamily="serif">N</text>
        </g>
      </svg>
    </div>
  );
}

// ─────────── Particle system ───────────
function spawnParticle(layer, x, y, kind = 'smoke', extra) {
  if (!layer) return;
  const p = document.createElement('div');
  p.style.cssText = `position:absolute;pointer-events:none;left:${x}px;top:${y}px;`;
  if (kind === 'smoke') {
    const size = 20 + Math.random() * 30;
    p.style.cssText += `
      width:${size}px;height:${size}px;border-radius:50%;
      background:radial-gradient(circle,rgba(220,200,180,0.7),transparent 70%);
      transform:translate(-50%,-50%);
      animation:smoke-rise ${1.2 + Math.random()*0.8}s ease-out forwards;`;
  } else if (kind === 'spark') {
    const size = 3 + Math.random() * 4;
    const angle = Math.random() * Math.PI * 2;
    const dist = 30 + Math.random() * 60;
    p.style.cssText += `
      width:${size}px;height:${size}px;border-radius:50%;
      background:#f5d889;box-shadow:0 0 ${size*2}px #f5d889;
      transform:translate(-50%,-50%);
      --dx:${Math.cos(angle)*dist}px;--dy:${Math.sin(angle)*dist}px;
      animation:spark-fly 0.6s ease-out forwards;`;
  } else if (kind === 'flash') {
    p.style.cssText += `
      width:80px;height:80px;border-radius:50%;
      background:radial-gradient(circle,rgba(255,240,200,1),rgba(255,200,100,0.3) 30%,transparent 70%);
      transform:translate(-50%,-50%);
      animation:flash-burst 0.4s ease-out forwards;`;
  } else if (kind === 'damage') {
    p.textContent = extra || '-1';
    p.style.cssText += `
      color:#ff5040;font-weight:900;font-size:32px;
      text-shadow:0 0 8px rgba(0,0,0,0.9),0 2px 0 #1a0a04;
      font-family:Georgia,serif;
      transform:translate(-50%,-50%);
      animation:damage-pop 0.7s ease-out forwards;`;
  }
  layer.appendChild(p);
  setTimeout(() => p.remove(), 1500);
}

// ─────────── Battlefield ───────────
function Battlefield({ theme, onSpeed }) {
  const speed = onSpeed || 1;
  const cardStyle = theme.cardStyle || 'oil';
  const bgKind = theme.bgKind || 'painting';
  const mood = theme.mood || 'cold';
  const p1Faction = theme.p1 || 'france';
  const p2Faction = theme.p2 || 'prussia';

  function buildDeck(faction) {
    const src = window.FACTION_DECKS[faction] || [];
    const deck = src.map((card, i) => ({
      ...card,
      faction,
      sourceId: `${faction}-${i}`,
    }));
    for (let i = deck.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [deck[i], deck[j]] = [deck[j], deck[i]];
    }
    const openingPlayableIdx = deck
      .slice(0, 4)
      .findIndex(card => card.kind !== 'event' && card.cost <= INITIAL_MORALE);
    if (openingPlayableIdx < 0) {
      const fallbackIdx = deck.findIndex(card => card.kind !== 'event' && card.cost <= INITIAL_MORALE);
      if (fallbackIdx >= 0) {
        const [fallback] = deck.splice(fallbackIdx, 1);
        const insertAt = Math.floor(Math.random() * 4);
        deck.splice(insertAt, 0, fallback);
      }
    }
    return deck;
  }

  const [turn, setTurn] = useState(1);
  const [activePlayer, setActivePlayer] = useState(1);
  const [p1HP, setP1HP] = useState(20);
  const [p2HP, setP2HP] = useState(20);
  const [p1Morale, setP1Morale] = useState(INITIAL_MORALE);
  const [p2Morale, setP2Morale] = useState(INITIAL_MORALE);
  const [hand, setHand] = useState([]);
  const [p1Deck, setP1Deck] = useState(() => buildDeck(p1Faction));
  const [p2Deck, setP2Deck] = useState(() => buildDeck(p2Faction));
  const [p1Discard, setP1Discard] = useState([]);
  const [p2Discard, setP2Discard] = useState([]);
  const [showDiscard, setShowDiscard] = useState(null);
  const [p2Hand, setP2Hand] = useState([1, 1, 1, 1]);
  // Board layout:
  //   p2.rear  (P2's rear, top row)
  //   p2.front (P2's front, second row — touches skirmish)
  //   skirmish.shared (one shared row, holds both p1 and p2 units mixed)
  //   p1.front (third row)
  //   p1.rear  (bottom row)
  const [board, setBoard] = useState({
    p2rear:   [null, null, null, null],
    p2front:  [null, null, null, null],
    skirmish: [null, null, null, null],
    p1front:  [null, null, null, null],
    p1rear:   [null, null, null, null],
  });
  const [draggingCard, setDraggingCard] = useState(null);
  const dragRef = useRef({ x: 0, y: 0, startX: 0, startY: 0, lifted: false });
  const ghostRef = useRef(null);
  const rafIdRef = useRef(null);
  const [hoveredSlot, setHoveredSlot] = useState(null);
  const [hoveredHandIndex, setHoveredHandIndex] = useState(-1);
  const [shakeAmp, setShakeAmp] = useState(0);
  const [flash, setFlash] = useState(false);
  const [turnBanner, setTurnBanner] = useState(null);
  const [endScreen, setEndScreen] = useState(null);
  const [attacking, setAttacking] = useState(null);

  const fxLayer = useRef(null);
  const stage = useRef(null);
  const handRef = useRef(null);
  const unitIdRef = useRef(1);
  const hoveredSlotRef = useRef(null);
  const { locked: animLocked, tryRun: tryRunAction } = useActionQueue();
  const targetingRef = useRef(null);
  const arrowRef = useRef(null);

  useEffect(() => {
    drawCards(4);
    setTurnBanner({ turn: 1, player: 1, skip: false });
    setTimeout(() => setTurnBanner(null), 600 / speed);
  }, []);

  function drawCards(n) {
    setP1Deck(deck => {
      const taken = deck.slice(0, n);
      const remain = deck.slice(n);
      const newCards = taken.map(t => ({
        ...t,
        id: 'c' + (unitIdRef.current++),
        owner: 'p1',
        drawing: true,
      }));
      if (newCards.length) setHand(h => [...h, ...newCards]);
      return remain;
    });
    setTimeout(() => setHand(h => h.map(c => ({ ...c, drawing: false }))), 600 / speed);
  }

  function drawP2Card() {
    const drawn = p2Deck[0] || null;
    if (!drawn) return null;
    setP2Deck(deck => deck.slice(1));
    return { ...drawn, id: 'e' + (unitIdRef.current++), owner: 'p2', faction: p2Faction };
  }

  function chooseP2PlayableCard() {
    const idx = p2Deck.findIndex(card => card.kind !== 'event' && card.cost <= p2Morale);
    if (idx < 0) return null;
    const drawn = p2Deck[idx];
    setP2Deck(deck => deck.filter((_, i) => i !== idx));
    return { ...drawn, id: 'e' + (unitIdRef.current++), owner: 'p2', faction: p2Faction };
  }

  function discardCard(card) {
    if (!card) return;
    const clean = { ...card, dead: false, justDeployed: false, drawing: false };
    if (clean.owner === 'p2') setP2Discard(d => [clean, ...d]);
    else setP1Discard(d => [clean, ...d]);
  }

  // Units enter from the rear line. Advancing to front/skirmish should be a
  // separate movement action in a later rules pass.
  function canP1Deploy(lineKey) {
    return lineKey === 'p1rear';
  }

  function onCardPointerDown(e, card) {
    if (card.cost > p1Morale || activePlayer !== 1) return;
    if (animLocked) return;
    e.preventDefault();
    const rect = stage.current.getBoundingClientRect();
    dragRef.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      startX: e.clientX,
      startY: e.clientY,
      lifted: false,
    };
    setDraggingCard(card);
  }

  useEffect(() => {
    if (!draggingCard) return;
    stage.current?.classList.add('drag-active');

    function onMove(e) {
      const rect = stage.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;
      if (!dragRef.current.lifted) {
        if (Math.hypot(dx, dy) <= 8) return;
        dragRef.current.lifted = true;
      }
      dragRef.current.x = x;
      dragRef.current.y = y;
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = requestAnimationFrame(() => {
        if (ghostRef.current) {
          ghostRef.current.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) rotate(-2deg) scale(1.1)`;
        }
      });
      const el = document.elementFromPoint(e.clientX, e.clientY);
      const slot = el?.closest('[data-slot]');
      const prev = hoveredSlotRef.current;
      const next = slot ? { line: slot.dataset.line, idx: parseInt(slot.dataset.idx) } : null;
      if (prev && (!next || prev.line !== next.line || prev.idx !== next.idx)) {
        const prevEl = document.querySelector(`[data-slot][data-line="${prev.line}"][data-idx="${prev.idx}"]`);
        if (prevEl) prevEl.classList.remove('slot-hover-valid');
      }
      if (next && canP1Deploy(next.line)) {
        slot.classList.add('slot-hover-valid');
      }
      hoveredSlotRef.current = next;
    }

    function onUp(e) {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      if (!dragRef.current.lifted) { cleanup(); return; }
      const el = document.elementFromPoint(e.clientX, e.clientY);
      const slot = el?.closest('[data-slot]');
      const dropSlot = slot ? { line: slot.dataset.line, idx: parseInt(slot.dataset.idx) } : hoveredSlotRef.current;
      if (dropSlot && draggingCard && canP1Deploy(dropSlot.line)) {
        const slotData = board[dropSlot.line][dropSlot.idx];
        if (!slotData) { deployCard(draggingCard, dropSlot.line, dropSlot.idx); cleanup(); return; }
      }
      // Bounce-back
      if (ghostRef.current) {
        const handCard = document.querySelector(`[data-hand-card="${draggingCard.id}"]`);
        if (handCard) {
          const cr = handCard.getBoundingClientRect();
          const sr = stage.current.getBoundingClientRect();
          const tx = cr.left + cr.width/2 - sr.left;
          const ty = cr.top + cr.height/2 - sr.top;
          ghostRef.current.style.transition = `transform 250ms var(--ease-rest)`;
          ghostRef.current.style.transform = `translate(${tx}px, ${ty}px) translate(-50%, -50%) rotate(0deg) scale(1.0)`;
          setTimeout(() => cleanup(), 250);
          return;
        }
      }
      cleanup();
    }

    function onKeyDown(e) {
      if (e.key === 'Escape') {
        if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
        cleanup();
      }
    }

    function cleanup() {
      document.querySelectorAll('.slot-hover-valid').forEach(el => el.classList.remove('slot-hover-valid'));
      hoveredSlotRef.current = null;
      setDraggingCard(null);
      stage.current?.classList.remove('drag-active');
    }

    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('keydown', onKeyDown);
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      stage.current?.classList.remove('drag-active');
    };
  }, [draggingCard, board, p1Morale, activePlayer]);

  function deployCard(card, line, idx) {
    tryRunAction((done) => {
      if (card.kind === 'event') {
        setHand(h => h.filter(c => c.id !== card.id));
        setP1Morale(m => m - card.cost);
        discardCard({ ...card, owner: 'p1' });
        spawnParticle(fxLayer.current, dragRef.current.x, dragRef.current.y, 'flash');
        done();
        return;
      }

      setBoard(b => {
        if (b[line][idx]) return b;
        const nextLine = [...b[line]];
        nextLine[idx] = { ...card, owner: 'p1', deployedTurn: turn, justDeployed: true };
        return { ...b, [line]: nextLine };
      });
      setHand(h => h.filter(c => c.id !== card.id));
      setP1Morale(m => m - card.cost);

      setTimeout(() => {
        const slotEl = document.querySelector(`[data-slot][data-line="${line}"][data-idx="${idx}"]`);
        if (slotEl) {
          const r = slotEl.getBoundingClientRect();
          const sr = stage.current.getBoundingClientRect();
          const cx = r.left + r.width/2 - sr.left;
          const cy = r.top + r.height/2 - sr.top;
          spawnParticle(fxLayer.current, cx, cy, 'flash');
          for (let i = 0; i < 8; i++) spawnParticle(fxLayer.current, cx, cy, 'spark');
          for (let i = 0; i < 5; i++) {
            setTimeout(() => spawnParticle(fxLayer.current, cx + (Math.random()-0.5)*40, cy + (Math.random()-0.5)*40, 'smoke'), i*60);
          }
        }
      }, 50);

      setTimeout(() => {
        setBoard(b => {
          const ln = b[line].map(u => u?.id === card.id ? { ...u, justDeployed: false } : u);
          return { ...b, [line]: ln };
        });
        done();
      }, 700 / speed);
    });
  }

  function nextP1Line(line) {
    if (line === 'p1rear') return 'p1front';
    if (line === 'p1front') return 'skirmish';
    return null;
  }

  function advanceUnit(fromLine, fromIdx, toLine, toIdx) {
    tryRunAction((done) => {
      setBoard(b => {
        const unit = b[fromLine][fromIdx];
        if (!unit || b[toLine][toIdx]) return b;
        const from = [...b[fromLine]];
        const to = [...b[toLine]];
        from[fromIdx] = null;
        to[toIdx] = { ...unit, justDeployed: false, hasAdvanced: true };
        return { ...b, [fromLine]: from, [toLine]: to };
      });
      setP1Morale(m => Math.max(0, m - 1));
      setTimeout(() => {
        const slotEl = document.querySelector(`[data-slot][data-line="${toLine}"][data-idx="${toIdx}"]`);
        if (slotEl && stage.current) {
          const r = slotEl.getBoundingClientRect();
          const sr = stage.current.getBoundingClientRect();
          spawnParticle(fxLayer.current, r.left+r.width/2-sr.left, r.top+r.height/2-sr.top, 'flash');
        }
        done();
      }, 40);
    });
  }

  useEffect(() => {
    if (animLocked || activePlayer !== 1) return;
    function onPointerDown(e) {
      const slot = e.target.closest('[data-slot]');
      if (!slot) return;
      const line = slot.dataset.line;
      const idx = parseInt(slot.dataset.idx);
      const unit = board[line]?.[idx];
      if (!unit || unit.owner !== 'p1' || unit.hasAdvanced) return;
      e.preventDefault();
      const rect = stage.current.getBoundingClientRect();
      targetingRef.current = { line, idx, originX: e.clientX - rect.left, originY: e.clientY - rect.top };
      if (arrowRef.current) arrowRef.current.style.display = 'block';
    }
    function onPointerMove(e) {
      if (!targetingRef.current) return;
      const rect = stage.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const { originX, originY } = targetingRef.current;
      const svg = arrowRef.current;
      if (svg) {
        const path = svg.querySelector('path');
        const cpX = (originX + x) / 2;
        const cpY = Math.min(originY, y) - 30;
        path.setAttribute('d', `M${originX},${originY} Q${cpX},${cpY} ${x},${y}`);
      }
    }
    function onPointerUp(e) {
      if (!targetingRef.current) return;
      const { line, idx } = targetingRef.current;
      if (arrowRef.current) arrowRef.current.style.display = 'none';
      const el = document.elementFromPoint(e.clientX, e.clientY);
      const slot = el?.closest('[data-slot]');
      const hq = el?.closest('[data-hq]');
      if (hq?.dataset.hq === 'p2') {
        attackTarget(line, idx, null, null);
      } else if (slot) {
        const tl = slot.dataset.line;
        const ti = parseInt(slot.dataset.idx);
        const tu = board[tl]?.[ti];
        if (tu?.owner === 'p2') {
          attackTarget(line, idx, tl, ti);
        } else if (!tu) {
          const nextLine = nextP1Line(line);
          if (nextLine === tl && idx === ti && p1Morale >= 1) {
            advanceUnit(line, idx, tl, ti);
          }
        }
      }
      targetingRef.current = null;
    }
    function onCancel() {
      targetingRef.current = null;
      if (arrowRef.current) arrowRef.current.style.display = 'none';
    }
    const el = stage.current;
    if (!el) return;
    el.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onCancel);
    return () => {
      el.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onCancel);
    };
  }, [animLocked, activePlayer, board, p1Morale]);

  function attackTarget(line, idx, targetLine, targetIdx) {
    tryRunAction((done) => {
      const unit = board[line][idx];
      if (!unit || unit.justDeployed || unit.owner !== 'p1') { done(); return; }
      const slotEl = document.querySelector(`[data-slot][data-line="${line}"][data-idx="${idx}"]`);
      const targetEl = targetLine
        ? document.querySelector(`[data-slot][data-line="${targetLine}"][data-idx="${targetIdx}"]`)
        : document.querySelector('[data-hq="p2"]');
      if (!slotEl || !targetEl) { done(); return; }
      const sr = stage.current.getBoundingClientRect();
      const a = slotEl.getBoundingClientRect();
      const t = targetEl.getBoundingClientRect();
      const dx = t.left - a.left;
      const dy = t.top - a.top;
      const dist = Math.hypot(dx, dy);

      // Stage 0: wind-up (0..80ms)
      const unitEl = slotEl.querySelector('[style]');
      if (unitEl) {
        unitEl.style.transition = `transform 80ms var(--ease-snap-in)`;
        unitEl.style.transform = `scale(0.95) rotate(${dx > 0 ? -5 : 5}deg)`;
      }

      // Stage 1: lunge (80..80+L ms)
      const L = Math.min(380, 240 + dist / 3);
      setTimeout(() => {
        setAttacking({ line, idx, dx: dx * 0.55, dy: dy * 0.55 });
        if (unitEl) {
          unitEl.style.transition = `transform ${L}ms var(--ease-overshoot)`;
          unitEl.style.transform = '';
        }
      }, 80 / speed);

      // Stage 2: freeze + impact (80+L ms)
      setTimeout(() => {
        const impactX = a.left + a.width/2 + dx*0.55 - sr.left;
        const impactY = a.top + a.height/2 + dy*0.55 - sr.top;
        spawnParticle(fxLayer.current, impactX, impactY, 'flash');
        for (let i = 0; i < 12; i++) spawnParticle(fxLayer.current, impactX, impactY, 'spark');
        for (let i = 0; i < 6; i++) {
          setTimeout(() => spawnParticle(fxLayer.current, impactX + (Math.random()-0.5)*30, impactY + (Math.random()-0.5)*30, 'smoke'), i*50);
        }
        const dmg = unit.atk;
        spawnParticle(fxLayer.current, impactX, impactY, 'damage', '-' + dmg);
        const amp = Math.min(12, 4 + dmg * 1.5);
        setShakeAmp(amp); setFlash(true);
        setTimeout(() => { setShakeAmp(0); setFlash(false); }, 200);

        if (targetLine) {
          setBoard(b => {
            const ln = [...b[targetLine]];
            const tgt = ln[targetIdx];
            if (!tgt) return b;
            const newHp = tgt.hp - dmg;
            if (newHp <= 0) {
              ln[targetIdx] = { ...tgt, hp: 0, dead: true };
              setTimeout(() => setBoard(bb => {
                const l2 = [...bb[targetLine]];
                discardCard(l2[targetIdx]);
                l2[targetIdx] = null;
                return { ...bb, [targetLine]: l2 };
              }), 420 / speed);
            } else {
              ln[targetIdx] = { ...tgt, hp: newHp };
            }
            return { ...b, [targetLine]: ln };
          });
        } else {
          setP2HP(h => Math.max(0, h - dmg));
        }
      }, (80 + L) / speed);

      // Stage 3: recoil (170+L ms)
      setTimeout(() => { setAttacking(null); }, (170 + L) / speed);

      // Stage 4: counter (390+L ms)
      if (targetLine) {
        setTimeout(() => {
          setBoard(b2 => {
            const tgt = b2[targetLine]?.[targetIdx];
            if (!tgt || tgt.dead) return b2;
            const counter = tgt.atk;
            const myLn = [...b2[line]];
            if (myLn[idx]) {
              myLn[idx] = { ...myLn[idx], hp: myLn[idx].hp - counter };
              if (myLn[idx].hp <= 0) {
                setTimeout(() => setBoard(bb => {
                  const l3 = [...bb[line]];
                  discardCard(l3[idx]);
                  l3[idx] = null;
                  return { ...bb, [line]: l3 };
                }), 420 / speed);
              }
            }
            return { ...b2, [line]: myLn };
          });
        }, (390 + L) / speed);
      }

      // Done
      setTimeout(() => { done(); }, (590 + L) / speed);
    });
  }

  function endTurn() {
    setActivePlayer(2);
    setTurnBanner({ turn, player: 2, skip: false });

    // Banner auto-dismiss after 600ms
    const bannerTimer = setTimeout(() => {
      setTurnBanner(null);
    }, 600 / speed);

    // AI deploy after 800ms (was 1500ms)
    setTimeout(() => {
      const u = chooseP2PlayableCard();
      setP2Hand(h => h.slice(1));
      if (!u) return;
      if (u?.kind === 'event') {
        setP2Morale(m => Math.max(0, m - Math.min(m, u.cost)));
        discardCard(u);
        return;
      }
      if (u.cost <= p2Morale) {
        const candidates = ['p2rear'];
        for (const ln of candidates) {
          const idx = board[ln].findIndex(s => !s);
          if (idx >= 0) {
            setBoard(b => {
              const next = [...b[ln]];
              next[idx] = { ...u, id: 'e' + (unitIdRef.current++), faction: p2Faction, owner: 'p2', justDeployed: true };
              return { ...b, [ln]: next };
            });
            setP2Morale(m => m - u.cost);
            const slotEl = document.querySelector(`[data-slot][data-line="${ln}"][data-idx="${idx}"]`);
            if (slotEl) {
              const r = slotEl.getBoundingClientRect();
              const sr = stage.current.getBoundingClientRect();
              spawnParticle(fxLayer.current, r.left+r.width/2-sr.left, r.top+r.height/2-sr.top, 'flash');
            }
            break;
          }
        }
      }
    }, 800 / speed);

    // Next turn after 3000/speed
    setTimeout(() => {
      clearTimeout(bannerTimer);
      const nextMorale = Math.min(MAX_MORALE, turn + 1);
      setTurnBanner(null);
      setActivePlayer(1);
      setTurn(t => t + 1);
      setP1Morale(nextMorale);
      setP2Morale(nextMorale);
      setBoard(b => {
        const resetLine = (line) => line.map(u => u?.owner === 'p1' ? { ...u, hasAdvanced: false } : u);
        return {
          ...b,
          p1rear: resetLine(b.p1rear),
          p1front: resetLine(b.p1front),
          skirmish: resetLine(b.skirmish),
        };
      });
      setP2Hand(h => [...h, 1]);
      setTurnBanner({ turn: turn + 1, player: 1, skip: false });
      drawCards(1);
      setTimeout(() => setTurnBanner(null), 600 / speed);
    }, 3000 / speed);
  }

  useEffect(() => {
    if (p1HP <= 0 && !endScreen) setEndScreen('defeat');
    else if (p2HP <= 0 && !endScreen) setEndScreen('victory');
  }, [p1HP, p2HP]);

  const f1 = window.FACTIONS[p1Faction];
  const f2 = window.FACTIONS[p2Faction];

  // Line definitions (top to bottom)
  const lineDefs = [
    { key: 'p2rear',   label: '后方 · ARRIÈRE',         owner: 'p2', kind: 'rear' },
    { key: 'p2front',  label: '前线 · LIGNE DE FRONT',   owner: 'p2', kind: 'front' },
    { key: 'skirmish', label: '散兵线 · TIRAILLEURS',    owner: 'shared', kind: 'skirmish' },
    { key: 'p1front',  label: '前线 · LIGNE DE FRONT',   owner: 'p1', kind: 'front' },
    { key: 'p1rear',   label: '后方 · ARRIÈRE',         owner: 'p1', kind: 'rear' },
  ];
  const boardFrame = {
    position: 'absolute',
    top: 100,
    bottom: 218,
    left: 92,
    right: 110,
    borderRadius: 6,
    overflow: 'hidden',
    border: `1px solid ${f1.gold}66`,
    boxShadow: '0 10px 32px rgba(0,0,0,0.45), inset 0 0 30px rgba(0,0,0,0.45)',
  };

  return (
    <div ref={stage} className={'battlefield-stage' + (shakeAmp > 0 ? ' shake' : '') + (draggingCard ? ' drag-active' : '')} style={{
      position: 'relative', width: '100%', height: '100%',
      borderRadius: 6, overflow: 'hidden',
      background: 'linear-gradient(180deg, #0e0a06 0%, #19100a 48%, #0e0a06 100%)',
      transform: shakeAmp > 0 ? `translate(${(Math.random()-0.5)*shakeAmp}px,${(Math.random()-0.5)*shakeAmp}px)` : 'none',
      transition: shakeAmp > 0 ? 'none' : 'transform 0.1s',
    }}>
      {/* HQ bars top + bottom */}
      <HQBar side="p2" faction={f2} hp={p2HP} morale={p2Morale} active={activePlayer===2}
        spinner={activePlayer===2 && !turnBanner}/>
      <HQBar side="p1" faction={f1} hp={p1HP} morale={p1Morale} active={activePlayer===1}/>

      {/* Central battlefield only: background + tactical lines live here. */}
      <div style={boardFrame}>
        <BattlefieldBg kind={bgKind} mood={mood}/>
        <div style={{
          position: 'absolute',
          inset: 8,
          display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          {lineDefs.map(def => (
          <Line key={def.key} def={def} board={board} hovered={hoveredSlot}
            f1={f1} f2={f2} cardStyle={cardStyle}
            attacking={attacking}
            speed={speed}
            canHover={!!draggingCard && canP1Deploy(def.key)}
          />
          ))}
        </div>
      </div>

      <SidePile
        side="left"
        label="弃牌区"
        faction={f1}
        cards={p1Discard}
        count={p1Discard.length}
        mode="discard"
        onClick={() => setShowDiscard('p1')}
      />
      <SidePile
        side="right"
        label="发牌区"
        faction={f1}
        cards={p1Deck}
        count={p1Deck.length}
        mode="deck"
      />

      {/* enemy hand (top) */}
      <div style={{position: 'absolute', top: 6, left: '50%', transform: 'translateX(-50%)', display: 'flex', height: 38, zIndex: 6}}>
        {p2Hand.map((_, i) => (
          <div key={i} style={{
            width: 34, height: 46, marginLeft: i ? -12 : 0,
            background: `linear-gradient(135deg, ${f2.primary}, #1a1410)`,
            border: `1.5px solid ${f2.gold}`, borderRadius: 3,
            transform: `rotate(${(i-1.5)*5}deg) translateY(${Math.abs(i-1.5)*2}px)`,
            boxShadow: '0 2px 4px rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div dangerouslySetInnerHTML={{__html: f2.crest(22)}}/>
          </div>
        ))}
      </div>

      {/* player hand */}
      <div ref={handRef} style={{
        position: 'absolute', bottom: 18, left: 0, right: 0, height: 138,
        display: 'flex', justifyContent: 'center', alignItems: 'flex-end',
        pointerEvents: 'none', zIndex: 7,
        background: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(10,7,4,0.55) 44%, rgba(10,7,4,0.86) 100%)',
      }}
      onMouseMove={(e) => {
        const cards = hand.filter(c => draggingCard?.id !== c.id);
        if (!cards.length) return;
        const rect = handRef.current.getBoundingClientRect();
        const cardW = 110 * 0.74;
        const overlap = 28;
        const step = cardW - overlap;
        const total = cardW + step * (cards.length - 1);
        const start = rect.left + (rect.width - total) / 2;
        const x = e.clientX - start;
        const idx = Math.max(0, Math.min(cards.length - 1, Math.round(x / step)));
        setHoveredHandIndex(idx);
      }}
      onMouseLeave={() => setHoveredHandIndex(-1)}
      >
        {hand.map((card, i) => {
          const N = hand.length;
          const angle = (i - (N-1)/2) * Math.min(8, 70 / N);
          const offY = Math.abs(i - (N-1)/2) * Math.min(6, 42 / N);
          const isHovered = hoveredHandIndex === i && !draggingCard;
          const isDragging = draggingCard?.id === card.id;
          if (isDragging) return null;
          return (
            <div key={card.id}
            data-hand-card={card.id}
            data-card-name={card.name}
            data-card-cost={card.cost}
            data-card-kind={card.kind || 'unit'}
            style={{
              position: 'relative',
              transform: `translateY(${card.drawing ? 200 : (isHovered ? -78 : offY)}px) rotate(${isHovered ? 0 : angle}deg) scale(${isHovered ? 1.45 : 1})`,
              transformOrigin: 'bottom center',
              transition: `transform ${0.4/speed}s cubic-bezier(.2,.8,.3,1)`,
              marginLeft: i ? -28 : 0,
              zIndex: isHovered ? 100 : i,
              pointerEvents: 'auto',
              cursor: card.cost <= p1Morale && activePlayer===1 ? 'grab' : 'not-allowed',
              opacity: card.cost > p1Morale ? 0.65 : 1,
              filter: isHovered ? 'drop-shadow(0 12px 24px rgba(0,0,0,0.8)) drop-shadow(0 0 20px rgba(212,165,92,0.4))' : 'drop-shadow(0 4px 6px rgba(0,0,0,0.5))',
            }}
            onPointerDown={(e) => onCardPointerDown(e, card)}
            >
              <window.Card style={cardStyle} unit={card} faction={card.faction} scale={0.74} onCard/>
            </div>
          );
        })}
      </div>

      {/* Hover preview — large card in top-right */}
      {hoveredHandIndex >= 0 && !draggingCard && hand[hoveredHandIndex] && (
        <div style={{
          position: 'absolute', right: 220, top: 80,
          zIndex: 200, pointerEvents: 'none',
          transform: 'scale(2.2)', transformOrigin: 'top right',
          filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.8))',
          transition: 'opacity var(--dur-hover) var(--ease-hover)',
        }}>
          <window.Card style={cardStyle} unit={hand[hoveredHandIndex]} faction={hand[hoveredHandIndex].faction} onCard/>
        </div>
      )}

      {/* dragging ghost */}
      {draggingCard && (
        <div ref={ghostRef} style={{
          position: 'absolute', left: 0, top: 0,
          transform: `translate(${dragRef.current.x}px, ${dragRef.current.y}px) translate(-50%, -50%) rotate(-2deg) scale(1.1)`,
          pointerEvents: 'none', zIndex: 999,
          filter: 'drop-shadow(0 16px 30px rgba(0,0,0,0.7))',
          willChange: 'transform',
        }}>
          <window.Card style={cardStyle} unit={draggingCard} faction={draggingCard.faction} onCard/>
        </div>
      )}

      {/* End turn */}
      <button onClick={endTurn} disabled={activePlayer !== 1} style={{
        position: 'absolute', right: 16, bottom: 150,
        background: activePlayer === 1
          ? `linear-gradient(180deg, #c8504c, #8b1a1a)`
          : `linear-gradient(180deg, #5a4530, #3a2818)`,
        color: '#f4ead0',
        border: `2px solid ${f1.gold}`,
        padding: '10px 16px',
        borderRadius: 4, cursor: activePlayer === 1 ? 'pointer' : 'default',
        fontFamily: 'Georgia, serif', fontWeight: 'bold',
        letterSpacing: 2, fontSize: 14,
        boxShadow: '0 4px 8px rgba(0,0,0,0.5)',
        zIndex: 80,
      }}>
        {activePlayer === 1 ? '结束回合' : '敌方回合'}
      </button>

      {flash && <div style={{position: 'absolute', inset: 0, background: 'rgba(255,240,200,0.4)', pointerEvents: 'none', zIndex: 50, animation: 'flash-fade 0.25s ease-out'}}/>}

      <div ref={fxLayer} style={{position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 60}}/>

      <svg ref={arrowRef} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 55, display: 'none' }}>
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#d4a55c" opacity="0.9"/>
          </marker>
        </defs>
        <path d="" fill="none" stroke="#d4a55c" strokeWidth="2.5" strokeDasharray="8,4" markerEnd="url(#arrowhead)" opacity="0.8"/>
      </svg>

      {turnBanner && <TurnBanner
        turn={turnBanner.turn}
        player={turnBanner.player}
        faction={turnBanner.player===1 ? f1 : f2}
        speed={speed}
        onSkip={() => setTurnBanner(null)}
      />}
      {endScreen && <EndScreen kind={endScreen} faction={f1}/>}
      {showDiscard && (
        <DiscardOverlay
          title={showDiscard === 'p1' ? '我方弃牌区' : '敌方弃牌区'}
          faction={showDiscard === 'p1' ? f1 : f2}
          cards={showDiscard === 'p1' ? p1Discard : p2Discard}
          cardStyle={cardStyle}
          onClose={() => setShowDiscard(null)}
        />
      )}
    </div>
  );
}

// ─────────── Side Piles ───────────
function SidePile({ side, label, faction, count, mode, onClick }) {
  const isLeft = side === 'left';
  const isDeck = mode === 'deck';
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      style={{
        position: 'absolute',
        top: '50%',
        [isLeft ? 'left' : 'right']: 12,
        width: 66,
        height: 132,
        transform: 'translateY(-50%)',
        border: `1.5px solid ${faction.gold}`,
        borderRadius: 5,
        background: 'rgba(10,8,6,0.72)',
        color: '#f4ead0',
        fontFamily: 'Georgia, serif',
        padding: 6,
        cursor: onClick ? 'pointer' : 'default',
        boxShadow: '0 6px 18px rgba(0,0,0,0.5), inset 0 0 16px rgba(0,0,0,0.5)',
        zIndex: 11,
      }}
    >
      <div style={{
        height: 88,
        borderRadius: 4,
        border: `1px ${isDeck ? 'solid' : 'dashed'} ${faction.gold}99`,
        background: isDeck
          ? `linear-gradient(135deg, ${faction.primary}, #1a1410)`
          : 'rgba(0,0,0,0.32)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {isDeck ? (
          <>
            <div style={{position: 'absolute', inset: 5, border: `1px solid ${faction.gold}55`, borderRadius: 3}} />
            <div dangerouslySetInnerHTML={{__html: faction.crest(34)}} />
          </>
        ) : (
          <div style={{fontSize: 28, color: faction.gold, opacity: 0.8}}>令</div>
        )}
      </div>
      <div style={{fontSize: 11, fontWeight: 'bold', marginTop: 6, letterSpacing: 1}}>{label}</div>
      <div style={{fontSize: 18, fontWeight: 900, color: faction.gold, lineHeight: 1.1}}>{count}</div>
    </button>
  );
}

function DiscardOverlay({ title, faction, cards, cardStyle, onClose }) {
  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      background: 'rgba(0,0,0,0.72)',
      zIndex: 210,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 42,
    }}>
      <div style={{
        width: 760,
        maxWidth: '86%',
        maxHeight: '78%',
        background: 'rgba(18,13,9,0.96)',
        border: `2px solid ${faction.gold}`,
        borderRadius: 6,
        boxShadow: '0 18px 60px rgba(0,0,0,0.7)',
        color: '#f4ead0',
        overflow: 'hidden',
      }}>
        <div style={{
          height: 46,
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: `1px solid ${faction.gold}66`,
          background: `linear-gradient(90deg, ${faction.primary}cc, rgba(0,0,0,0.2))`,
        }}>
          <div style={{fontSize: 16, fontWeight: 900, letterSpacing: 2}}>{title} · {cards.length}</div>
          <button type="button" onClick={onClose} style={{
            width: 30,
            height: 30,
            borderRadius: 4,
            border: `1px solid ${faction.gold}`,
            background: 'rgba(0,0,0,0.25)',
            color: '#f4ead0',
            cursor: 'pointer',
            fontSize: 18,
          }}>×</button>
        </div>
        <div style={{
          padding: 18,
          overflowY: 'auto',
          maxHeight: 'calc(78vh - 46px)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(92px, 1fr))',
          gap: 12,
          justifyItems: 'center',
        }}>
          {cards.length === 0 ? (
            <div style={{gridColumn: '1 / -1', padding: 36, color: '#a08560'}}>弃牌区为空</div>
          ) : cards.map((card, i) => (
            <window.Card key={`${card.id || card.sourceId || card.name}-${i}`}
              style={cardStyle}
              unit={card}
              faction={card.faction}
              scale={0.72}
              onCard
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────── HQ Bar ───────────
function HQBar({ side, faction, hp, morale, active, spinner = false }) {
  const top = side === 'p2';
  return (
    <div data-hq={side} data-morale={morale} style={{
      position: 'absolute',
      [top ? 'top' : 'bottom']: top ? 56 : 142,
      left: 92, right: 110,
      height: 36, padding: '4px 12px',
      background: `linear-gradient(90deg, ${faction.primary}cc 0%, rgba(0,0,0,0.6) 100%)`,
      borderTop: `1px solid ${faction.gold}`,
      borderRight: `1px solid ${faction.gold}`,
      borderBottom: `1px solid ${faction.gold}`,
      borderLeft: `4px solid ${faction.gold}`,
      borderRadius: 3,
      display: 'flex', alignItems: 'center', gap: 14,
      color: '#f4ead0', fontFamily: 'Georgia, serif',
      boxShadow: active ? `0 0 16px ${faction.gold}88, inset 0 0 12px rgba(0,0,0,0.4)` : 'inset 0 0 12px rgba(0,0,0,0.4)',
      cursor: 'default',
      zIndex: 5,
    }}>
      <div dangerouslySetInnerHTML={{__html: faction.crest(28)}}/>
      {spinner && (
        <div style={{
          width: 16, height: 16,
          border: `2px solid ${faction.gold}44`,
          borderTopColor: faction.gold,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          flexShrink: 0,
        }}/>
      )}
      <div style={{flex: 1}}>
        <div style={{fontSize: 13, fontWeight: 'bold'}}>{faction.name}</div>
        <div style={{fontSize: 9, color: faction.gold, fontStyle: 'italic'}}>{faction.leader} · {faction.leaderTitle}</div>
      </div>
      <div style={{display: 'flex', gap: 18, fontSize: 11}}>
        <div>
          <div style={{color: faction.gold, fontSize: 9, letterSpacing: 1}}>HQ</div>
          <div style={{fontSize: 18, fontWeight: 900, color: hp < 8 ? '#ff5040' : '#f4ead0'}}>{hp}</div>
        </div>
        <div>
          <div style={{color: faction.gold, fontSize: 9, letterSpacing: 1}}>军令</div>
          <div style={{fontSize: 18, fontWeight: 900}}>{morale}/10</div>
        </div>
      </div>
    </div>
  );
}

// ─────────── Line ───────────
function Line({ def, board, hovered, f1, f2, cardStyle, attacking, speed, canHover }) {
  const { key, label, owner, kind } = def;
  const slots = board[key];
  // Visual treatment per line kind
  const lineBg = kind === 'skirmish'
    ? `linear-gradient(to bottom, rgba(180,120,60,0.10), rgba(120,80,40,0.10))`
    : kind === 'front'
      ? `linear-gradient(to bottom, ${owner==='p1' ? 'rgba(74,111,165,0.10)' : 'rgba(139,26,26,0.10)'}, rgba(0,0,0,0.18))`
      : `rgba(0,0,0,0.18)`;
  const borderColor = owner === 'p1' ? `${f1.gold}66` : owner === 'p2' ? `${f2.gold}66` : `${f1.gold}33`;
  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'stretch', gap: 6,
      background: lineBg,
      border: `1px ${kind === 'skirmish' ? 'dashed' : 'solid'} ${borderColor}`,
      borderRadius: 3,
      padding: '2px 8px',
      position: 'relative',
      minHeight: 0,
      overflow: 'hidden',
    }}>
      {/* line label */}
      <div style={{
        writingMode: 'vertical-rl', textOrientation: 'mixed',
        width: 22,
        color: owner === 'p1' ? f1.gold : owner === 'p2' ? f2.gold : '#a08560',
        fontSize: 8, letterSpacing: 1,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        textShadow: '0 1px 2px #000', flexShrink: 0,
        overflow: 'hidden',
      }}>{label}</div>
      {/* 4 slots */}
      <div style={{flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6, justifyItems: 'center', alignItems: 'center'}}>
        {slots.map((u, i) => (
          <Slot key={i} line={key} idx={i} unit={u}
            f1={f1} f2={f2}
            ownerLine={owner}
            hovered={hovered?.line===key && hovered?.idx===i}
            cardStyle={cardStyle}
            attacking={attacking?.line===key && attacking?.idx===i ? attacking : null}
            speed={speed}
            canHover={canHover}
            kind={kind}
          />
        ))}
      </div>
    </div>
  );
}

// ─────────── Slot ───────────
function Slot({ line, idx, unit, f1, f2, ownerLine, hovered, cardStyle, attacking, speed, canHover, kind }) {
  const isP2Unit = unit?.owner === 'p2';
  const transform = attacking
    ? `translate(${attacking.dx}px, ${attacking.dy}px) scale(1.05)`
    : 'none';
  return (
    <div data-slot data-line={line} data-idx={idx}
      data-unit-id={unit?.id || ''}
      data-unit-owner={unit?.owner || ''}
      data-unit-name={unit?.name || ''}
      style={{
      width: 66, height: 66,
      border: hovered && canHover
        ? `2px solid ${f1.gold}`
        : `1px dashed ${kind === 'skirmish' ? 'rgba(212,165,92,0.4)' : (ownerLine === 'p1' ? `${f1.gold}55` : `${f2.gold}55`)}`,
      borderRadius: 3,
      background: hovered && canHover ? `${f1.gold}30` : 'rgba(0,0,0,0.25)',
      boxShadow: hovered && canHover ? `0 0 16px ${f1.gold}88` : 'inset 0 0 12px rgba(0,0,0,0.35)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      transition: 'border-color 0.15s, background 0.15s, box-shadow 0.15s',
      position: 'relative',
      cursor: 'default',
    }}>
      {unit && (
        <div
          style={{
            transform: `${isP2Unit ? 'rotate(180deg) ' : ''}${transform}`,
            transition: attacking ? `transform ${0.28/speed}s cubic-bezier(.5,-0.4,.5,1.4)` : `transform ${0.4/speed}s ease-out`,
            cursor: unit.owner === 'p1' && !unit.hasAdvanced ? 'grab' : 'default',
            animation: unit.justDeployed ? `card-deploy ${0.6/speed}s ease-out` : 'none',
            filter: unit.dead ? 'opacity(0.5) grayscale(1)' : (unit.justDeployed ? `drop-shadow(0 0 12px ${f1.gold})` : 'none'),
          }}>
          <window.Card style={cardStyle} unit={unit} faction={unit.faction}
            damaged={unit.hp < (window.FACTION_DECKS[unit.faction]?.find(c => c.name === unit.name)?.hp || unit.hp)}
            dead={unit.dead}
            scale={0.42} onCard/>
        </div>
      )}
    </div>
  );
}

// ─────────── Turn Banner ───────────
function TurnBanner({ turn, player, faction, speed, onSkip }) {
  return (
    <div onClick={onSkip} style={{
      position: 'absolute', inset: 0, display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'auto', zIndex: 90, cursor: 'pointer',
      animation: `banner-sweep ${2/speed}s ease-out forwards`,
    }}>
      <div style={{
        background: `linear-gradient(90deg, transparent 0%, ${faction.primary}f0 20%, ${faction.primary}f0 80%, transparent 100%)`,
        borderTop: `2px solid ${faction.gold}`,
        borderBottom: `2px solid ${faction.gold}`,
        padding: '14px 80px', textAlign: 'center',
        color: '#f4ead0', fontFamily: 'Georgia, serif',
        boxShadow: `0 0 30px ${faction.gold}aa`,
        minWidth: '70%',
      }}>
        <div style={{fontSize: 14, color: faction.gold, letterSpacing: 6, marginBottom: 4}}>
          ── 第 {turn} 回合 · TURN {turn} ──
        </div>
        <div style={{fontSize: 26, fontWeight: 900, letterSpacing: 4, textShadow: '0 2px 4px rgba(0,0,0,0.8)'}}>
          {player === 1 ? '我方行动' : '敌方行动'}
        </div>
        <div style={{fontSize: 11, color: faction.gold, marginTop: 4, fontStyle: 'italic'}}>{faction.motto}</div>
      </div>
    </div>
  );
}

// ─────────── End Screen ───────────
function EndScreen({ kind, faction }) {
  const isWin = kind === 'victory';
  return (
    <div style={{
      position: 'absolute', inset: 0,
      background: `radial-gradient(ellipse at center, ${isWin ? 'rgba(20,40,20,0.85)' : 'rgba(40,10,10,0.9)'}, rgba(0,0,0,0.95))`,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      zIndex: 200, color: '#f4ead0',
      animation: 'end-fade 0.8s ease-out',
    }}>
      <div style={{fontSize: 80, marginBottom: 12, color: isWin ? faction.gold : '#8b6f47'}}>
        {isWin ? (
          <svg width="100" height="100" viewBox="0 0 100 100">
            <defs>
              <radialGradient id="medal-grad" cx="0.3" cy="0.3"><stop offset="0" stopColor="#f5d889"/><stop offset="1" stopColor="#8b6f1e"/></radialGradient>
            </defs>
            <path d="M50,15 L60,35 L60,55 L50,65 L40,55 L40,35 Z" fill="#8b1a1a"/>
            <circle cx="50" cy="65" r="22" fill="url(#medal-grad)" stroke="#3a2818" strokeWidth="2"/>
            <path d="M50,52 L53,62 L63,62 L55,68 L58,78 L50,72 L42,78 L45,68 L37,62 L47,62 Z" fill="#3a2818"/>
          </svg>
        ) : (
          <svg width="100" height="100" viewBox="0 0 100 100">
            <path d="M30,30 Q30,15 50,15 Q70,15 70,30 L70,55 Q70,60 65,60 L60,60 L60,70 L40,70 L40,60 L35,60 Q30,60 30,55 Z" fill="#8b6f47"/>
            <circle cx="40" cy="38" r="4" fill="#1a0a04"/><circle cx="60" cy="38" r="4" fill="#1a0a04"/>
            <path d="M45,50 Q50,53 55,50" fill="none" stroke="#1a0a04" strokeWidth="2"/>
          </svg>
        )}
      </div>
      <div style={{fontSize: 48, fontWeight: 900, letterSpacing: 12, color: isWin ? faction.gold : '#c2552c', textShadow: '0 4px 8px rgba(0,0,0,0.8)', fontFamily: 'Georgia, serif'}}>
        {isWin ? '胜  利' : '败  北'}
      </div>
      <div style={{fontSize: 14, color: '#a08560', marginTop: 8, letterSpacing: 4, fontStyle: 'italic'}}>
        {isWin ? 'VICTOIRE · ' + faction.motto : 'DÉFAITE'}
      </div>
    </div>
  );
}

window.Battlefield = Battlefield;
