import { useCallback } from 'react';

type HapticPattern = number | number[];

export const useHaptic = () => {
  const vibrate = useCallback((pattern: HapticPattern = 10) => {
    if ('vibrate' in navigator) {
      navigator.vibrate(pattern);
    }
  }, []);

  const light = useCallback(() => vibrate(10), [vibrate]);
  const medium = useCallback(() => vibrate(20), [vibrate]);
  const heavy = useCallback(() => vibrate(30), [vibrate]);
  const success = useCallback(() => vibrate([10, 50, 10]), [vibrate]);
  const warning = useCallback(() => vibrate([20, 100, 20]), [vibrate]);
  const error = useCallback(() => vibrate([30, 100, 30, 100, 30]), [vibrate]);

  return {
    vibrate,
    light,
    medium,
    heavy,
    success,
    warning,
    error,
  };
};