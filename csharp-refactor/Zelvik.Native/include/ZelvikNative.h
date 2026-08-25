#pragma once

#include <stdint.h>

#ifdef ZELVIK_NATIVE_EXPORTS
#define ZELVIK_NATIVE_API __declspec(dllexport)
#else
#define ZELVIK_NATIVE_API __declspec(dllimport)
#endif

extern "C"
{
    ZELVIK_NATIVE_API int ZelvikNative_GetVersion();

    // Creates a single-producer/single-consumer audio ring buffer.
    //
    // capacityFrames:
    //     Maximum number of audio frames stored.
    //
    // bytesPerFrame:
    //     Size of one complete PCM frame.
    //
    // Returns an opaque handle, or nullptr on failure.
    ZELVIK_NATIVE_API void* ZelvikNative_AudioBuffer_Create(
        uint32_t capacityFrames,
        uint32_t bytesPerFrame);

    ZELVIK_NATIVE_API void ZelvikNative_AudioBuffer_Destroy(
        void* handle);

    // Writes complete audio frames into the buffer.
    // Returns the number of frames actually written.
    ZELVIK_NATIVE_API uint32_t ZelvikNative_AudioBuffer_Write(
        void* handle,
        const void* data,
        uint32_t frameCount);

    // Reads complete audio frames from the buffer.
    // Returns the number of frames actually read.
    ZELVIK_NATIVE_API uint32_t ZelvikNative_AudioBuffer_Read(
        void* handle,
        void* data,
        uint32_t frameCount);

    ZELVIK_NATIVE_API uint32_t ZelvikNative_AudioBuffer_AvailableFrames(
        void* handle);

    ZELVIK_NATIVE_API uint32_t ZelvikNative_AudioBuffer_CapacityFrames(
        void* handle);
}