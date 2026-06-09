"use client";

import React, { useState, useEffect, useRef } from "react";
import api from "../lib/api";

interface SymbolData {
  symbol: string;
  name: string;
}

interface SymbolAutocompleteProps {
  value: string;
  onChange: (val: string) => void;
  onSelect?: (val: string) => void;
  placeholder?: string;
  className?: string;
}

export default function SymbolAutocomplete({
  value,
  onChange,
  onSelect,
  placeholder = "Hisse Kodu (Örn: THYAO)",
  className = "",
}: SymbolAutocompleteProps) {
  const [symbols, setSymbols] = useState<SymbolData[]>([]);
  const [filtered, setFiltered] = useState<SymbolData[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Component mount olduğunda sembolleri çek
    api.get("/market/symbols")
      .then((res) => {
        if (res.data?.symbols) {
          setSymbols(res.data.symbols);
        }
      })
      .catch((err) => console.error("Semboller çekilemedi:", err));
  }, []);

  useEffect(() => {
    // Dışarı tıklandığında menüyü kapat
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.toUpperCase();
    onChange(val); // Parent'a bildir (böylece input değeri değişir)

    if (val.length > 0) {
      // Hem sembolde hem isimde ara
      const results = symbols.filter(
        (s) =>
          s.symbol.startsWith(val) ||
          s.name.toUpperCase().startsWith(val)
      );
      // Sadece 50 sonuç göster (performans için)
      setFiltered(results.slice(0, 50));
      setIsOpen(true);
      setFocusedIndex(-1);
    } else {
      setFiltered([]);
      setIsOpen(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : prev));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (focusedIndex >= 0 && focusedIndex < filtered.length) {
        selectSymbol(filtered[focusedIndex].symbol);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const selectSymbol = (sym: string) => {
    onChange(sym);
    setIsOpen(false);
    if (onSelect) {
      onSelect(sym);
    }
  };

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (value.length > 0 && filtered.length > 0) setIsOpen(true);
        }}
        placeholder={placeholder}
        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors uppercase"
      />
      
      {isOpen && filtered.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filtered.map((item, index) => (
            <li
              key={item.symbol}
              onClick={() => selectSymbol(item.symbol)}
              onMouseEnter={() => setFocusedIndex(index)}
              className={`px-4 py-2 cursor-pointer flex flex-col justify-center ${
                index === focusedIndex ? "bg-blue-600/50" : "hover:bg-gray-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">{item.symbol}</span>
              </div>
              <span className="text-xs text-gray-400 truncate">{item.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
