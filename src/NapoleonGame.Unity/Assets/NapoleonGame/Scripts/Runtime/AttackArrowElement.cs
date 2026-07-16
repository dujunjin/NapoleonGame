using UnityEngine;
using UnityEngine.UIElements;

namespace NapoleonGame.Runtime
{
    public sealed class AttackArrowElement : VisualElement
    {
        private Vector2 _start;
        private Vector2 _end;
        private Color _color = new Color(0.95f, 0.72f, 0.28f, 0.95f);

        public AttackArrowElement()
        {
            pickingMode = PickingMode.Ignore;
            AddToClassList("attack-arrow");
            generateVisualContent += DrawArrow;
        }

        public void SetPoints(Vector2 start, Vector2 end, Color? color = null)
        {
            _start = start;
            _end = end;
            if (color.HasValue)
            {
                _color = color.Value;
            }
            MarkDirtyRepaint();
        }

        private void DrawArrow(MeshGenerationContext context)
        {
            var delta = _end - _start;
            if (delta.sqrMagnitude < 4f)
            {
                return;
            }

            var direction = delta.normalized;
            var perpendicular = new Vector2(-direction.y, direction.x);
            var tip = _end;
            var basePoint = tip - direction * 22f;

            var painter = context.painter2D;
            painter.strokeColor = _color;
            painter.lineWidth = 5f;
            painter.BeginPath();
            painter.MoveTo(_start);
            painter.LineTo(basePoint);
            painter.Stroke();

            painter.fillColor = _color;
            painter.BeginPath();
            painter.MoveTo(tip);
            painter.LineTo(basePoint + perpendicular * 9f);
            painter.LineTo(basePoint - perpendicular * 9f);
            painter.ClosePath();
            painter.Fill();
        }
    }
}
