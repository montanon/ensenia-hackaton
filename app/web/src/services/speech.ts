// Web Speech API service for speech-to-text
export class SpeechRecognitionService {
  private recognition: any = null;
  private isSupported: boolean = false;
  private isActive: boolean = false; // Track if user is actively listening
  private restartTimeoutId: number | null = null;

  constructor() {
    // Check for browser support
    if (typeof window === 'undefined') {
      this.isSupported = false;
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.isSupported = true;
      this.setupRecognition();
    }
  }

  private setupRecognition() {
    if (!this.recognition) return;

    // Configure recognition
    this.recognition.lang = 'es-CL'; // Chilean Spanish
    this.recognition.continuous = true; // Keep listening for continuous input
    this.recognition.interimResults = true; // Get interim results
    this.recognition.maxAlternatives = 1;
    console.log('[Speech] Recognition configured - continuous mode enabled');
  }

  isAvailable(): boolean {
    return this.isSupported;
  }

  start(
    onResult: (transcript: string, isFinal: boolean) => void,
    onError?: (error: string) => void,
    onEnd?: () => void
  ): void {
    console.log('[Speech] start() called');
    if (!this.recognition) {
      console.error('[Speech] Recognition not available');
      onError?.('Speech recognition not supported');
      return;
    }

    this.isActive = true;
    this.clearRestartTimeout();

    this.recognition.onresult = (event: any) => {
      console.log('[Speech] onresult event - results length:', event.results.length);
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript;
      const isFinal = result.isFinal;
      console.log('[Speech] Result received:', { transcript, isFinal, confidence: result[0].confidence });

      onResult(transcript, isFinal);

      // Restart listening if still active to keep the mic open
      if (this.isActive && isFinal) {
        console.log('[Speech] Restarting recognition to keep mic open');
        this.restartTimeoutId = window.setTimeout(() => {
          if (this.isActive && this.recognition) {
            try {
              this.recognition.start();
              console.log('[Speech] Recognition restarted');
            } catch (err) {
              console.error('[Speech] Failed to restart:', err);
            }
          }
        }, 100);
      }
    };

    this.recognition.onerror = (event: any) => {
      console.error('[Speech] Recognition error:', event.error);

      // Don't restart on network errors - they indicate unavailable service
      if (event.error === 'network') {
        console.error('[Speech] Network error - speech recognition service unavailable. Make sure you have internet connection.');
        if (this.isActive) {
          onError?.('Speech recognition service unavailable. Check your internet connection.');
          this.isActive = false;
        }
        return;
      }

      if (event.error !== 'no-speech') {
        onError?.(event.error);
      }

      // Restart on no-speech errors if still active
      if (this.isActive && event.error === 'no-speech') {
        console.log('[Speech] No speech detected, restarting...');
        this.restartTimeoutId = window.setTimeout(() => {
          if (this.isActive && this.recognition) {
            try {
              this.recognition.start();
            } catch (err) {
              console.error('[Speech] Failed to restart after no-speech:', err);
            }
          }
        }, 100);
      }
    };

    this.recognition.onend = () => {
      console.log('[Speech] Recognition ended, isActive:', this.isActive);

      // If still active, restart to keep mic open
      if (this.isActive) {
        console.log('[Speech] Restarting recognition on end');
        this.restartTimeoutId = window.setTimeout(() => {
          if (this.isActive && this.recognition) {
            try {
              this.recognition.start();
              console.log('[Speech] Recognition restarted on end');
            } catch (err) {
              console.error('[Speech] Failed to restart on end:', err);
            }
          }
        }, 100);
      } else {
        onEnd?.();
      }
    };

    try {
      console.log('[Speech] Starting recognition...');
      this.recognition.start();
    } catch (err) {
      console.error('[Speech] Failed to start:', err);
      onError?.('Failed to start recording');
    }
  }

  stop(): void {
    console.log('[Speech] stop() called');
    this.isActive = false;
    this.clearRestartTimeout();
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.error('[Speech] Error stopping:', err);
      }
    }
  }

  abort(): void {
    console.log('[Speech] abort() called');
    this.isActive = false;
    this.clearRestartTimeout();
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (err) {
        console.error('[Speech] Error aborting:', err);
      }
    }
  }

  private clearRestartTimeout(): void {
    if (this.restartTimeoutId !== null) {
      clearTimeout(this.restartTimeoutId);
      this.restartTimeoutId = null;
    }
  }
}

export const speechRecognitionService = new SpeechRecognitionService();
