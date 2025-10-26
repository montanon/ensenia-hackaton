/**
 * Audio Recording Service
 *
 * Handles microphone capture and audio chunk streaming via WebSocket.
 * Uses MediaRecorder API for browser-native audio capture.
 */

export interface AudioRecordingOptions {
  mimeType?: string;
  audioBitsPerSecond?: number;
  onChunkReceived?: (chunk: string) => void; // base64 encoded
  onError?: (error: Error) => void;
}

export class AudioRecordingService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private isRecording = false;
  private chunks: Blob[] = [];
  private onChunkReceived?: (chunk: string) => void;
  private onError?: (error: Error) => void;

  constructor(options: AudioRecordingOptions = {}) {
    this.onChunkReceived = options.onChunkReceived;
    this.onError = options.onError;
  }

  /**
   * Check if browser supports audio recording
   */
  static isSupported(): boolean {
    return !!(
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === 'function' &&
      typeof window.MediaRecorder !== 'undefined'
    );
  }

  /**
   * Get supported MIME types for audio recording
   */
  static getSupportedMimeTypes(): string[] {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/wav',
      'audio/aac',
    ];

    return types.filter(type => MediaRecorder.isTypeSupported(type));
  }

  /**
   * Start recording audio from microphone
   */
  async startRecording(): Promise<void> {
    try {
      if (this.isRecording) {
        console.warn('Recording is already in progress');
        return;
      }

      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create audio context (optional, for advanced processing)
      try {
        const AudioContextClass = window.AudioContext || 
          (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        this.audioContext = AudioContextClass ? new AudioContextClass() : null;
      } catch (error) {
        console.warn('Failed to create AudioContext:', error);
        this.audioContext = null;
      }

      // Create MediaRecorder
      const supportedTypes = AudioRecordingService.getSupportedMimeTypes();
      const mimeType = supportedTypes[0] || 'audio/webm';
      
      console.log('[AudioRecording] Supported MIME types:', supportedTypes);
      console.log('[AudioRecording] Using MIME type:', mimeType);

      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      this.chunks = [];
      this.isRecording = true;
      
      console.log('[AudioRecording] MediaRecorder created with:', {
        mimeType: this.mediaRecorder.mimeType,
        audioBitsPerSecond: 128000,
        state: this.mediaRecorder.state,
      });

      // Handle data available events - send chunks via callback
      this.mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          this.chunks.push(event.data);
          console.log('[AudioRecording] Chunk received:', {
            size: event.data.size,
            type: event.data.type,
            totalChunks: this.chunks.length,
          });

          // Convert blob to base64 and send
          this.blobToBase64(event.data)
            .then(base64 => {
              if (this.onChunkReceived) {
                this.onChunkReceived(base64);
              }
            })
            .catch((err) => {
              console.error('Failed to convert audio chunk to base64:', err);
              this.onError?.(err);
            });
        }
      };

      // Start recording with timeslice to get chunks periodically
      this.mediaRecorder.start(500); // Request data every 500ms

      console.log('Audio recording started');
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      console.error('Failed to start recording:', err);
      this.onError?.(err);
      throw err;
    }
  }

  /**
   * Stop recording and return complete audio blob
   */
  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || !this.isRecording) {
        reject(new Error('No active recording'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        if (!this.mediaRecorder) {
          reject(new Error('MediaRecorder was destroyed during stop'));
          return;
        }
        const blob = new Blob(this.chunks, { type: this.mediaRecorder.mimeType });
        this.cleanup();
        resolve(blob);
      };

      this.mediaRecorder.onerror = (event: Event) => {
        const mediaRecorderEvent = event as ErrorEvent;
        const error = new Error(`Recording error: ${mediaRecorderEvent.message || 'Unknown error'}`);
        this.cleanup();
        reject(error);
      };

      this.mediaRecorder.stop();
      this.isRecording = false;
    });
  }

  /**
   * Pause recording
   */
  pauseRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.pause();
      this.isRecording = false;
      console.log('Audio recording paused');
    }
  }

  /**
   * Resume recording after pause
   */
  resumeRecording(): void {
    if (this.mediaRecorder && !this.isRecording) {
      this.mediaRecorder.resume();
      this.isRecording = true;
      console.log('Audio recording resumed');
    }
  }

  /**
   * Check if currently recording
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Get current recording duration in seconds
   */
  getRecordingDuration(): number {
    if (!this.audioContext) return 0;
    return this.audioContext.currentTime;
  }

  /**
   * Convert blob to base64 string
   */
  private async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = (reader.result as string).split(',')[1];
        resolve(base64String);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Clean up resources
   */
  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.mediaRecorder = null;
    this.chunks = [];
    this.isRecording = false;
  }

  /**
   * Abort recording and clean up
   */
  abort(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
    }
    this.cleanup();
    console.log('Audio recording aborted');
  }
}

/**
 * Create and return a singleton instance of AudioRecordingService
 */
export function getAudioRecordingService(
  options?: AudioRecordingOptions
): AudioRecordingService {
  return new AudioRecordingService(options);
}
