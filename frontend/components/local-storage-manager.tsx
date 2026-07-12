
import { useEffect } from 'react';

interface LocalStorageManagerProps {
  id: string;
}

export function LocalStorageManager({ id }: LocalStorageManagerProps) {
  useEffect(() => {
    if (!id) return;
    try {
      localStorage.setItem('latestAssessmentId', id);
      
      // Keep a historical list of assessments as well, so judges can toggle between past runs!
      const historyRaw = localStorage.getItem('assessmentHistory');
      let history: string[] = [];
      if (historyRaw) {
        history = JSON.parse(historyRaw);
      }
      if (!history.includes(id)) {
        history.unshift(id);
        // Limit history to top 8 items to keep things clean
        history = history.slice(0, 8);
        localStorage.setItem('assessmentHistory', JSON.stringify(history));
      }
    } catch (e) {
      console.warn('Local storage not accessible: ', e);
    }
  }, [id]);

  return null;
}