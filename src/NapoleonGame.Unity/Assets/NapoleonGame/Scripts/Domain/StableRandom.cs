using System;

namespace NapoleonGame.Domain
{
    internal sealed class StableRandom
    {
        private uint _state;

        public StableRandom(int seed)
        {
            _state = unchecked((uint)seed) + 0x9E3779B9u;
            if (_state == 0)
            {
                _state = 0xA341316Cu;
            }
        }

        public int Next(int exclusiveMax)
        {
            if (exclusiveMax <= 0)
            {
                throw new ArgumentOutOfRangeException(nameof(exclusiveMax));
            }

            var value = NextUInt();
            return (int)(value % (uint)exclusiveMax);
        }

        private uint NextUInt()
        {
            var value = _state;
            value ^= value << 13;
            value ^= value >> 17;
            value ^= value << 5;
            _state = value;
            return value;
        }
    }
}
