using System;
using System.IO;
using NapoleonGame.Domain;
using NapoleonGame.Runtime;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;

namespace NapoleonGame.Editor
{
    public static class ProjectBootstrap
    {
        public const string ScenePath = "Assets/NapoleonGame/Scenes/Battle.unity";
        public const string PanelSettingsPath = "Assets/NapoleonGame/UI/BattlePanelSettings.asset";
        public const string CatalogPath = "Assets/NapoleonGame/Data/card_catalog.json";
        public const string ScreenPath = "Assets/NapoleonGame/UI/BattleScreen.uxml";
        public const string ThemePath = "Assets/NapoleonGame/UI/BattleTheme.uss";
        public const string FontPath = "Assets/NapoleonGame/Fonts/NotoSansCJKsc-Regular.otf";
        public const string FontAssetPath = "Assets/NapoleonGame/Fonts/NotoSansCJKsc-Regular SDF.asset";

        [MenuItem("Napoleon Game/Configure Playable Scene")]
        public static void ConfigureProject()
        {
            EnsureFolder("Assets/NapoleonGame", "Scenes");
            CreateOrLoadFontAsset();
            AssetDatabase.ImportAsset(ThemePath, ImportAssetOptions.ForceUpdate);
            var panelSettings = CreateOrLoadPanelSettings();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            scene.name = "Battle";

            var cameraObject = new GameObject("Main Camera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.025f, 0.04f, 0.055f, 1f);
            camera.orthographic = true;
            cameraObject.tag = "MainCamera";

            var application = new GameObject("Napoleon Game");
            var document = application.AddComponent<UIDocument>();
            document.panelSettings = panelSettings;
            document.visualTreeAsset = RequiredAsset<VisualTreeAsset>(ScreenPath);
            document.sortingOrder = 0;

            var bootstrap = application.AddComponent<GameBootstrap>();
            var serialized = new SerializedObject(bootstrap);
            serialized.FindProperty("cardCatalogJson").objectReferenceValue = RequiredAsset<UnityEngine.TextAsset>(CatalogPath);
            serialized.FindProperty("battleScreen").objectReferenceValue = RequiredAsset<VisualTreeAsset>(ScreenPath);
            serialized.FindProperty("battleTheme").objectReferenceValue = RequiredAsset<StyleSheet>(ThemePath);
            serialized.FindProperty("initialPlayerFaction").enumValueIndex = (int)Faction.France;
            serialized.FindProperty("initialEnemyFaction").enumValueIndex = (int)Faction.Prussia;
            serialized.FindProperty("initialSeed").intValue = 1977;
            serialized.ApplyModifiedPropertiesWithoutUndo();

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };

            PlayerSettings.companyName = "Napoleon Game Studio";
            PlayerSettings.productName = "Napoleon: Lines of Command";
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.runInBackground = true;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.usePlayerLog = true;
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, ScriptingImplementation.Mono2x);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("Playable battle scene configured at " + ScenePath);
        }

        [MenuItem("Napoleon Game/Build/macOS Development Build")]
        public static void BuildMacDevelopment()
        {
            ConfigureProject();
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName;
            var repositoryRoot = Directory.GetParent(Directory.GetParent(projectRoot)?.FullName ?? projectRoot)?.FullName;
            if (string.IsNullOrEmpty(repositoryRoot))
            {
                throw new InvalidOperationException("无法解析仓库根目录。");
            }

            var output = Path.Combine(repositoryRoot, "output", "unity", "NapoleonLinesOfCommand.app");
            Directory.CreateDirectory(Path.GetDirectoryName(output) ?? repositoryRoot);
            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = output,
                target = BuildTarget.StandaloneOSX,
                options = BuildOptions.Development
            };
            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
            {
                throw new InvalidOperationException("Unity 构建失败：" + report.summary.result + "，错误 " + report.summary.totalErrors);
            }

            Debug.Log("Build succeeded: " + output + " (" + report.summary.totalSize + " bytes)");
        }

        public static void ConfigureFromCommandLine()
        {
            try
            {
                ConfigureProject();
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }

        public static void BuildMacFromCommandLine()
        {
            try
            {
                BuildMacDevelopment();
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }

        private static PanelSettings CreateOrLoadPanelSettings()
        {
            var panelSettings = AssetDatabase.LoadAssetAtPath<PanelSettings>(PanelSettingsPath);
            if (panelSettings == null)
            {
                panelSettings = ScriptableObject.CreateInstance<PanelSettings>();
                AssetDatabase.CreateAsset(panelSettings, PanelSettingsPath);
            }

            panelSettings.name = "BattlePanelSettings";
            panelSettings.scaleMode = PanelScaleMode.ScaleWithScreenSize;
            panelSettings.referenceResolution = new Vector2Int(1920, 1080);
            panelSettings.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight;
            panelSettings.match = 0.5f;
            panelSettings.clearColor = true;
            panelSettings.colorClearValue = new Color(0.025f, 0.04f, 0.055f, 1f);
            panelSettings.targetTexture = null;
            EditorUtility.SetDirty(panelSettings);
            return panelSettings;
        }

        private static FontAsset CreateOrLoadFontAsset()
        {
            var fontAsset = AssetDatabase.LoadAssetAtPath<FontAsset>(FontAssetPath);
            if (fontAsset != null)
            {
                return fontAsset;
            }

            var sourceFont = RequiredAsset<Font>(FontPath);
            fontAsset = FontAsset.CreateFontAsset(sourceFont);
            if (fontAsset == null)
            {
                throw new InvalidOperationException("无法从 Noto Sans CJK SC 创建 TextCore 字体资产。");
            }

            fontAsset.name = "NotoSansCJKsc-Regular SDF";
            fontAsset.atlasPopulationMode = AtlasPopulationMode.Dynamic;
            fontAsset.isMultiAtlasTexturesEnabled = true;
            AssetDatabase.CreateAsset(fontAsset, FontAssetPath);

            if (fontAsset.material != null && !AssetDatabase.Contains(fontAsset.material))
            {
                fontAsset.material.name = fontAsset.name + " Material";
                AssetDatabase.AddObjectToAsset(fontAsset.material, fontAsset);
            }
            foreach (var texture in fontAsset.atlasTextures)
            {
                if (texture != null && !AssetDatabase.Contains(texture))
                {
                    texture.name = fontAsset.name + " Atlas";
                    AssetDatabase.AddObjectToAsset(texture, fontAsset);
                }
            }

            EditorUtility.SetDirty(fontAsset);
            AssetDatabase.SaveAssets();
            return fontAsset;
        }

        private static T RequiredAsset<T>(string path) where T : UnityEngine.Object
        {
            var asset = AssetDatabase.LoadAssetAtPath<T>(path);
            if (asset == null)
            {
                throw new InvalidOperationException("缺少 Unity 资源：" + path);
            }
            return asset;
        }

        private static void EnsureFolder(string parent, string child)
        {
            var path = parent + "/" + child;
            if (!AssetDatabase.IsValidFolder(path))
            {
                AssetDatabase.CreateFolder(parent, child);
            }
        }
    }
}
