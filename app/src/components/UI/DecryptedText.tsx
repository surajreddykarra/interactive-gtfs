'use client';

import { useState, useEffect } from 'react';

interface DecryptedTextProps {
  text: string;
  className?: string;
  speed?: number;
  maxIterations?: number;
}

const CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+';

export default function DecryptedText({ 
  text, 
  className = '', 
  speed = 50, 
  maxIterations = 10 
}: DecryptedTextProps) {
  const [displayText, setDisplayText] = useState(text);
  const [iteration, setIteration] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (iteration < text.length) {
      interval = setInterval(() => {
        setDisplayText(prev => 
          text
            .split('')
            .map((char, index) => {
              if (index < iteration) {
                return text[index];
              }
              return CHARACTERS[Math.floor(Math.random() * CHARACTERS.length)];
            })
            .join('')
        );
        setIteration(prev => prev + 1 / 3); // Slow down the reveal
      }, speed);
    } else {
      setDisplayText(text);
    }

    return () => clearInterval(interval);
  }, [text, iteration, speed]);

  return <span className={className}>{displayText}</span>;
}
