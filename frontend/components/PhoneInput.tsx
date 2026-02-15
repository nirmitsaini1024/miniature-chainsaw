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
    <div className="w-full relative">
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
          position: relative;
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
          color: #1e293b !important;
          font-weight: 500;
          cursor: pointer;
        }
        .phone-input .PhoneInputCountrySelectArrow {
          color: #64748b !important;
          opacity: 0.8;
        }
        /* Country dropdown menu */
        .PhoneInputCountrySelect--focus .PhoneInputCountrySelect {
          color: #1e293b !important;
        }
        /* Dropdown list styling */
        .PhoneInputCountryOptions {
          max-height: 300px;
          overflow-y: auto;
          background: white !important;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          z-index: 9999;
          position: absolute !important;
          top: 100% !important;
          left: 0 !important;
          right: auto !important;
          margin-top: 0.25rem;
          width: auto;
          min-width: 200px;
          max-width: 90vw;
        }
        /* Ensure dropdown stays within viewport */
        .PhoneInputCountry {
          position: relative;
        }
        .PhoneInputCountryOption {
          color: #1e293b !important;
          padding: 0.5rem 0.75rem;
          cursor: pointer;
        }
        .PhoneInputCountryOption:hover {
          background: #f1f5f9 !important;
        }
        .PhoneInputCountryOption--selected {
          background: #eff6ff !important;
          color: #1e40af !important;
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
          .phone-input .PhoneInputCountrySelect {
            color: #f1f5f9 !important;
          }
          .PhoneInputCountryOptions {
            background: #1e293b !important;
            border-color: #334155;
          }
          .PhoneInputCountryOption {
            color: #f1f5f9 !important;
          }
          .PhoneInputCountryOption:hover {
            background: #334155 !important;
          }
          .PhoneInputCountryOption--selected {
            background: #1e3a8a !important;
            color: #93c5fd !important;
          }
        }
      `}</style>
    </div>
  );
}

