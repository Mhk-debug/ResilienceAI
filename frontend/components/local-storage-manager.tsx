import { useEffect } from 'react';

interface LocalStorageManagerProps {
  id: string;
}

export function LocalStorageManager({ id }: LocalStorageManagerProps) {
  useEffect(() => {
    if (!id) return;
    try {
      localStorage.setItem('latestAssessmentId', id);
    } catch (e) {
      console.warn('Local storage not accessible: ', e);
    }
  }, [id]);

  return null;
}
