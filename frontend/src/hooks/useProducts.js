import { useState, useEffect } from 'react';
import { getProducts } from '../api/products';

export function useProducts(params = {}) {
  const [products, setProducts] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const paramsKey = JSON.stringify(params);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getProducts(params)
      .then(({ data }) => {
        if (!cancelled) {
          setProducts(data.results || data);
          setCount(data.count || (data.results || data).length);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [paramsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  return { products, count, loading, error };
}
