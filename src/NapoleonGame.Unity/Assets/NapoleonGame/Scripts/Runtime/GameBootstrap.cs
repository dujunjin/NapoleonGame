using System.Collections;
using NapoleonGame.Domain;
using UnityEngine;
using UnityEngine.UIElements;

namespace NapoleonGame.Runtime
{
    [RequireComponent(typeof(UIDocument))]
    public sealed class GameBootstrap : MonoBehaviour
    {
        [SerializeField] private TextAsset cardCatalogJson;
        [SerializeField] private VisualTreeAsset battleScreen;
        [SerializeField] private StyleSheet battleTheme;
        [SerializeField] private Faction initialPlayerFaction = Faction.France;
        [SerializeField] private Faction initialEnemyFaction = Faction.Prussia;
        [SerializeField] private int initialSeed = 1977;

        private UIDocument _document;
        private CardCatalog _catalog;
        private GameEngine _engine;
        private AiAgent _ai;
        private BattleScreenController _screen;
        private Coroutine _commandRoutine;
        private bool _initialized;
        private Faction _lastPlayerFaction;
        private Faction _lastEnemyFaction;
        private int _lastSeed;

        public GameEngine Engine => _engine;

        private void Start()
        {
            Initialize();
        }

        private void Initialize()
        {
            if (_initialized)
            {
                return;
            }

            _document = GetComponent<UIDocument>();
            if (_document.visualTreeAsset == null && battleScreen != null)
            {
                _document.visualTreeAsset = battleScreen;
            }

            var root = _document.rootVisualElement;
            if (root.Q<VisualElement>("battle-root") == null && battleScreen != null)
            {
                battleScreen.CloneTree(root);
            }
            if (battleTheme != null && !root.styleSheets.Contains(battleTheme))
            {
                root.styleSheets.Add(battleTheme);
            }

            Application.targetFrameRate = 60;
            _catalog = CardCatalogLoader.Load(cardCatalogJson);
            _ai = new AiAgent();
            _screen = new BattleScreenController(root, QueueCommand, StartNewMatch, RequestRematch);
            _initialized = true;
            StartNewMatch(initialPlayerFaction, initialEnemyFaction, initialSeed);
            root.Focus();
        }

        private void QueueCommand(GameCommand command)
        {
            if (_commandRoutine != null || _engine == null || command == null)
            {
                return;
            }

            _commandRoutine = StartCoroutine(ExecutePlayerAndAi(command));
        }

        private IEnumerator ExecutePlayerAndAi(GameCommand playerCommand)
        {
            _screen.SetInputLocked(true);
            yield return ExecuteOne(playerCommand);

            var safety = 0;
            while (!_engine.State.IsEnded && _engine.State.ActivePlayerId == 1 && safety < 80)
            {
                if (!_screen.ReducedMotion)
                {
                    yield return new WaitForSecondsRealtime(0.07f);
                }
                var command = _ai.Choose(_engine, 1);
                yield return ExecuteOne(command);
                safety += 1;
            }

            if (safety >= 80 && !_engine.State.IsEnded)
            {
                Debug.LogError("AI 单回合行动超过安全上限。");
                _screen.ShowToast("敌军命令循环异常，已中止该回合。 ");
            }

            _screen.SetInputLocked(_engine.State.IsEnded || _engine.State.ActivePlayerId != 0);
            _commandRoutine = null;
        }

        private IEnumerator ExecuteOne(GameCommand command)
        {
            var result = _engine.Execute(command);
            if (!result.Succeeded)
            {
                _screen.ShowToast(result.Reason);
                yield break;
            }

            _screen.Render(_engine);
            _screen.SetInputLocked(true);
            var longestDelay = 0f;
            foreach (var gameEvent in result.Events)
            {
                longestDelay = Mathf.Max(longestDelay, _screen.AnimateEvent(gameEvent));
            }
            if (longestDelay > 0f)
            {
                yield return new WaitForSecondsRealtime(longestDelay);
            }
        }

        private void StartNewMatch(Faction playerFaction, Faction enemyFaction, int seed)
        {
            if (!_initialized)
            {
                return;
            }

            if (_commandRoutine != null)
            {
                StopCoroutine(_commandRoutine);
                _commandRoutine = null;
            }

            _lastPlayerFaction = playerFaction;
            _lastEnemyFaction = enemyFaction;
            _lastSeed = seed;
            _engine = new GameEngine(_catalog);
            var result = _engine.StartMatch(playerFaction, enemyFaction, seed);
            if (!result.Succeeded)
            {
                _screen.ShowToast(result.Reason);
                return;
            }

            _screen.HideSetup();
            _screen.HideResult();
            _screen.ClearLog();
            _screen.SetInputLocked(false);
            _screen.Render(_engine);
            foreach (var gameEvent in result.Events)
            {
                _screen.AppendEvent(gameEvent);
            }
            _screen.ShowTurnBanner(0, 1);
        }

        private void RequestRematch()
        {
            StartNewMatch(_lastPlayerFaction, _lastEnemyFaction, _lastSeed + 1);
        }
    }
}
