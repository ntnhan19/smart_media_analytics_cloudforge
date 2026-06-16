const HISTORY_KEY = 'semantic_search_history';

export const getSearchHistory = () => {
  try {
    const raw = sessionStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
};

export const addSearchHistory = (query) => {
  if (!query || !query.trim()) return [];
  
  const currentHistory = getSearchHistory();
  const trimmedQuery = query.trim();
  
  // Don't add if it's the exact same as the most recent one
  if (currentHistory[0] === trimmedQuery) return currentHistory;
  
  // Remove duplicates and add to front, max 5 items
  const newHistory = [trimmedQuery, ...currentHistory.filter(q => q !== trimmedQuery)].slice(0, 5);
  
  sessionStorage.setItem(HISTORY_KEY, JSON.stringify(newHistory));
  return newHistory;
};

export const clearSearchHistory = () => {
  sessionStorage.removeItem(HISTORY_KEY);
};
