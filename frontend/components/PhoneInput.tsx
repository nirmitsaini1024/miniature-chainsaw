"use client";

import { useState } from "react";
import PhoneInputWithCountry from "react-phone-number-input";
import "react-phone-number-input/style.css";

interface PhoneInputProps {
  value: string;
  onChange: (value: string | undefined) => void;
  disabled?: boolean;
}

export default function PhoneInput({ value, onChange, disabled }: PhoneInputProps) {
  return (
    <div className="w-full">
      <PhoneInputWithCountry
        international
        defaultCountry="IN"
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="phone-input"
      />
      <style jsx global>{`
        .phone-input {
          width: 100%;
        }
        .phone-input .PhoneInputInput {
          width: 100%;
          padding: 0.75rem 1rem;
          border: 2px solid #e2e8f0;
          border-radius: 0.75rem;
          font-size: 1rem;
          color: #1e293b;
          background: white;
          transition: all 0.2s ease;
        }
        .phone-input .PhoneInputInput:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .phone-input .PhoneInputCountry {
          margin-right: 0.75rem;
          padding-left: 0.5rem;
        }
        .phone-input .PhoneInputCountrySelect {
          border: none;
          background: transparent;
        }
        @media (prefers-color-scheme: dark) {
          .phone-input .PhoneInputInput {
            background: #1e293b;
            border-color: #334155;
            color: #f1f5f9;
          }
          .phone-input .PhoneInputInput:focus {
            border-color: #3b82f6;
          }
        }
      `}</style>
    </div>
  );
}

