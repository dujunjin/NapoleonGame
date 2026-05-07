const { useState } = React;

const MATCHUPS = [
  {
    id: 'france-prussia',
    label: '法兰西 vs 普鲁士',
    bgKind: 'painting',
    cardStyle: 'oil',
    mood: 'dusk',
    p1: 'france',
    p2: 'prussia',
  },
  {
    id: 'france-russia',
    label: '法兰西 vs 俄罗斯',
    bgKind: 'painting',
    cardStyle: 'oil',
    mood: 'night',
    p1: 'france',
    p2: 'russia',
  },
  {
    id: 'prussia-russia',
    label: '普鲁士 vs 俄罗斯',
    bgKind: 'sandtable',
    cardStyle: 'heraldry',
    mood: 'warm',
    p1: 'prussia',
    p2: 'russia',
  },
];

function App() {
  if (!window.useTweaks || !window.Battlefield) {
    return <div style={{padding:40,color:'#f4ead0',fontFamily:'monospace'}}>Loading visual prototype...</div>;
  }

  const [tweaks, setTweak] = window.useTweaks(window.TWEAK_DEFAULTS);
  const [matchupId, setMatchupId] = useState(MATCHUPS[0].id);
  const matchup = MATCHUPS.find(m => m.id === matchupId) || MATCHUPS[0];

  return (
    <div style={{position: 'relative', width: '100vw', height: '100vh', background: '#0e0a06'}}>
      <window.Battlefield
        key={matchup.id}
        theme={{
          bgKind: tweaks.bgKind === 'default' ? matchup.bgKind : tweaks.bgKind,
          cardStyle: tweaks.cardStyle === 'default' ? matchup.cardStyle : tweaks.cardStyle,
          mood: tweaks.mood === 'default' ? matchup.mood : tweaks.mood,
          p1: matchup.p1,
          p2: matchup.p2,
        }}
        onSpeed={tweaks.speed}
      />

      <div style={{
        position: 'absolute',
        left: 16,
        top: 12,
        zIndex: 300,
        display: 'flex',
        gap: 8,
        background: 'rgba(0,0,0,0.46)',
        border: '1px solid rgba(212,165,92,0.35)',
        borderRadius: 5,
        padding: 6,
        backdropFilter: 'blur(8px)',
      }}>
        {MATCHUPS.map(m => (
          <button
            key={m.id}
            type="button"
            onClick={() => setMatchupId(m.id)}
            style={{
              height: 28,
              padding: '0 10px',
              borderRadius: 4,
              border: `1px solid ${m.id === matchup.id ? '#d4a55c' : 'rgba(212,165,92,0.35)'}`,
              background: m.id === matchup.id ? 'rgba(139,58,31,0.86)' : 'rgba(0,0,0,0.25)',
              color: '#f4ead0',
              fontSize: 12,
              cursor: 'pointer',
              fontFamily: '"Hiragino Sans", "Microsoft YaHei", sans-serif',
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      <window.TweaksPanel title="Tweaks">
        <window.TweakSection label="战场背景">
          <window.TweakRadio
            label="背景类型"
            value={tweaks.bgKind}
            options={[
              {value: 'default', label: '按对局'},
              {value: 'painting', label: '战画'},
              {value: 'sandtable', label: '沙盘'},
              {value: 'map', label: '地图'},
            ]}
            onChange={v => setTweak('bgKind', v)}
          />
          <window.TweakSelect
            label="色调"
            value={tweaks.mood}
            options={[
              {value: 'default', label: '按对局默认'},
              {value: 'warm', label: '暖棕'},
              {value: 'cold', label: '冷蓝'},
              {value: 'dusk', label: '黄昏'},
              {value: 'night', label: '夜战'},
            ]}
            onChange={v => setTweak('mood', v)}
          />
        </window.TweakSection>

        <window.TweakSection label="卡牌样式">
          <window.TweakRadio
            label="卡面"
            value={tweaks.cardStyle}
            options={[
              {value: 'default', label: '按对局'},
              {value: 'oil', label: '油画'},
              {value: 'heraldry', label: '纹章'},
              {value: 'minimal', label: '极简'},
            ]}
            onChange={v => setTweak('cardStyle', v)}
          />
        </window.TweakSection>

        <window.TweakSection label="动画">
          <window.TweakSlider
            label="动画速度"
            value={tweaks.speed}
            min={0.3}
            max={3}
            step={0.1}
            onChange={v => setTweak('speed', v)}
          />
        </window.TweakSection>
      </window.TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
