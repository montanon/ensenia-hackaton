// Web Speech API service for speech-to-text
export class SpeechRecognitionService {
  private recognition: any = null;
  private isSupported: boolean = false;

  constructor() {
    // Check for browser support
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
    this.recognition.continuous = false; // Stop after one result
    this.recognition.interimResults = true; // Get interim results
    this.recognition.maxAlternatives = 1;
  }

  isAvailable(): boolean {
    return this.isSupported;
  }

  start(
    onResult: (transcript: string, isFinal: boolean) => void,
    onError?: (error: string) => void,
    onEnd?: () => void
  ): void {
    if (!this.recognition) {
      onError?.('Speech recognition not supported');
      return;
    }

    this.recognition.onresult = (event: any) => {
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript;
      const isFinal = result.isFinal;

      onResult(transcript, isFinal);
    };

    this.recognition.onerror = (event: any) => {
      console.error('[Speech] Recognition error:', event.error);
      onError?.(event.error);
    };

    this.recognition.onend = () => {
      onEnd?.();
    };

    try {
      this.recognition.start();
    } catch (err) {
      console.error('[Speech] Failed to start:', err);
      onError?.('Failed to start recording');
    }
  }

  stop(): void {
    if (this.recognition) {
      this.recognition.stop();
    }
  }

  abort(): void {
    if (this.recognition) {
      this.recognition.abort();
    }
  }
}

export const speechRecognitionService = new SpeechRecognitionService();
