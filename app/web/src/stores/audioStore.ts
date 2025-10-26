import { create } from 'zustand';

interface AudioStore {
  currentAudio: string | null;
  isPlaying: boolean;
  isSpeaking: boolean;
  playbackSpeed: number;

  setCurrentAudio: (audioUrl: string | null) => void;
  setPlaying: (playing: boolean) => void;
  setSpeaking: (speaking: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  stopAudio: () => void;
}

export const useAudioStore = create<AudioStore>((set) => ({
  currentAudio: null,
  isPlaying: false,
  isSpeaking: false,
  playbackSpeed: 1.0,

  setCurrentAudio: (audioUrl) => set({ currentAudio: audioUrl }),

  setPlaying: (playing) => set({ isPlaying: playing }),

  setSpeaking: (speaking) => set({ isSpeaking: speaking }),

  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),

  stopAudio: () => set({
    currentAudio: null,
    isPlaying: false,
    isSpeaking: false
  }),
}));
