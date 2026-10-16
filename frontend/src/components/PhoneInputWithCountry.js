import React, { useState, useEffect } from 'react';
import { Phone, ChevronDown } from 'lucide-react';
import { Input } from './ui/input';

export const COUNTRY_CODES = [
  { code: '+263', country: 'ZW', name: 'Zimbabwe', flag: '🇿🇼', example: '77 123 4567' },
  { code: '+27', country: 'ZA', name: 'South Africa', flag: '🇿🇦', example: '82 123 4567' },
  { code: '+260', country: 'ZM', name: 'Zambia', flag: '🇿🇲', example: '97 123 4567' },
  { code: '+267', country: 'BW', name: 'Botswana', flag: '🇧🇼', example: '71 123 456' },
  { code: '+258', country: 'MZ', name: 'Mozambique', flag: '🇲🇿', example: '84 123 4567' },
  { code: '+264', country: 'NA', name: 'Namibia', flag: '🇳🇦', example: '81 123 4567' },
  { code: '+254', country: 'KE', name: 'Kenya', flag: '🇰🇪', example: '712 345678' },
  { code: '+234', country: 'NG', name: 'Nigeria', flag: '🇳🇬', example: '802 123 4567' },
  { code: '+44', country: 'GB', name: 'United Kingdom', flag: '🇬🇧', example: '7911 123456' },
  { code: '+1', country: 'US', name: 'USA / Canada', flag: '🇺🇸', example: '202 555 0123' },
  { code: '+61', country: 'AU', name: 'Australia', flag: '🇦🇺', example: '412 345 678' },
  { code: '+91', country: 'IN', name: 'India', flag: '🇮🇳', example: '98765 43210' },
  { code: '+971', country: 'AE', name: 'UAE', flag: '🇦🇪', example: '50 123 4567' },
];

/**
 * Reusable PhoneInputWithCountry component.
 * Allows user to choose country code via dropdown and enter national phone number.
 * Outputs full E.164 international format via `onChange(fullE164)`.
 */
export default function PhoneInputWithCountry({
  value = '',
  onChange,
  disabled = false,
  required = false,
  id = 'phone-input',
  placeholder,
  className = ''
}) {
  const [selectedCode, setSelectedCode] = useState('+263');
  const [nationalNumber, setNationalNumber] = useState('');

  // Synchronize incoming value if already in international format
  useEffect(() => {
    if (!value) {
      setNationalNumber('');
      return;
    }
    // Check if value starts with a known country code
    const matched = COUNTRY_CODES.find((c) => value.startsWith(c.code));
    if (matched) {
      setSelectedCode(matched.code);
      setNationalNumber(value.slice(matched.code.length).replace(/^0+/, ''));
    } else if (value.startsWith('+')) {
      // Unknown international code
      setNationalNumber(value.replace(/^\+\d+/, ''));
    } else {
      setNationalNumber(value.replace(/^0+/, ''));
    }
  }, []);

  const handleCountryChange = (e) => {
    const newCode = e.target.value;
    setSelectedCode(newCode);
    emitChange(newCode, nationalNumber);
  };

  const handleNumberChange = (e) => {
    let clean = e.target.value.replace(/[^\d\s-]/g, '');
    setNationalNumber(clean);
    emitChange(selectedCode, clean);
  };

  const emitChange = (code, rawNumber) => {
    // Strip leading zero and formatting
    const digitsOnly = rawNumber.replace(/\D/g, '').replace(/^0+/, '');
    const fullNumber = digitsOnly ? `${code}${digitsOnly}` : '';
    if (onChange) {
      onChange(fullNumber, { countryCode: code, nationalNumber: digitsOnly });
    }
  };

  const currentCountry = COUNTRY_CODES.find((c) => c.code === selectedCode) || COUNTRY_CODES[0];

  return (
    <div className={`flex rounded-xl overflow-hidden border border-white/10 bg-zinc-900/60 focus-within:border-blue-500/50 transition-colors ${className}`}>
      {/* Country Code Prefix Dropdown */}
      <div className="relative flex items-center bg-zinc-800/80 border-r border-white/10 px-3 cursor-pointer hover:bg-zinc-800 transition-colors">
        <span className="text-base mr-1.5 select-none">{currentCountry.flag}</span>
        <select
          value={selectedCode}
          onChange={handleCountryChange}
          disabled={disabled}
          className="bg-transparent text-sm font-semibold text-zinc-200 outline-none cursor-pointer appearance-none pr-5 z-10"
          aria-label="Select country code"
        >
          {COUNTRY_CODES.map((c) => (
            <option key={c.code} value={c.code} className="bg-zinc-900 text-zinc-100">
              {c.flag} {c.code} ({c.name})
            </option>
          ))}
        </select>
        <ChevronDown className="w-3.5 h-3.5 text-zinc-400 absolute right-2 pointer-events-none" />
      </div>

      {/* National Phone Number Input */}
      <div className="relative flex-1 flex items-center">
        <Phone className="w-4 h-4 text-zinc-500 absolute left-3 pointer-events-none" />
        <Input
          id={id}
          type="tel"
          disabled={disabled}
          required={required}
          value={nationalNumber}
          onChange={handleNumberChange}
          placeholder={placeholder || `e.g. ${currentCountry.example}`}
          className="w-full bg-transparent border-0 pl-9 pr-3 h-11 text-zinc-100 placeholder:text-zinc-600 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm font-medium"
        />
      </div>
    </div>
  );
}
