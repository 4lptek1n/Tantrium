import { useEffect } from "react";
import { useLocation } from "wouter";

export function AnalyzePage() {
  const [, setLocation] = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const dataset = params.get("dataset");
    const target = dataset ? `/hunt?dataset=${dataset}` : "/hunt";
    setLocation(target);
  }, [setLocation]);

  return null;
}
