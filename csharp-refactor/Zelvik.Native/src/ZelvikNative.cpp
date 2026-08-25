#include "ZelvikNative.h"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>
#include <new>
#include <vector>

namespace
{
    class AudioRingBuffer
    {
    public:
        AudioRingBuffer(
            uint32_t capacityFrames,
            uint32_t bytesPerFrame)
            : m_capacityFrames(capacityFrames),
              m_bytesPerFrame(bytesPerFrame),
              m_buffer(
                  static_cast<size_t>(capacityFrames) *
                  static_cast<size_t>(bytesPerFrame))
        {
        }

        uint32_t Write(
            const void* data,
            uint32_t frameCount)
        {
            if (!data || frameCount == 0)
            {
                return 0;
            }

            const uint32_t available =
                m_capacityFrames -
                (m_writePosition.load(std::memory_order_relaxed) -
                 m_readPosition.load(std::memory_order_acquire));

            const uint32_t framesToWrite =
                frameCount < available ? frameCount : available;

            if (framesToWrite == 0)
            {
                return 0;
            }

            const uint32_t writeIndex =
                m_writePosition.load(std::memory_order_relaxed) %
                m_capacityFrames;

            const uint32_t firstFrames =
                std::min(
                    framesToWrite,
                    m_capacityFrames - writeIndex);

            std::memcpy(
                m_buffer.data() +
                    static_cast<size_t>(writeIndex) *
                    m_bytesPerFrame,
                data,
                static_cast<size_t>(firstFrames) *
                m_bytesPerFrame);

            if (firstFrames < framesToWrite)
            {
                std::memcpy(
                    m_buffer.data(),
                    static_cast<const uint8_t*>(data) +
                        static_cast<size_t>(firstFrames) *
                        m_bytesPerFrame,
                    static_cast<size_t>(framesToWrite - firstFrames) *
                    m_bytesPerFrame);
            }

            m_writePosition.fetch_add(
                framesToWrite,
                std::memory_order_release);

            return framesToWrite;
        }

        uint32_t Read(
            void* data,
            uint32_t frameCount)
        {
            if (!data || frameCount == 0)
            {
                return 0;
            }

            const uint32_t available =
                m_writePosition.load(std::memory_order_acquire) -
                m_readPosition.load(std::memory_order_relaxed);

            const uint32_t framesToRead =
                frameCount < available ? frameCount : available;

            if (framesToRead == 0)
            {
                return 0;
            }

            const uint32_t readIndex =
                m_readPosition.load(std::memory_order_relaxed) %
                m_capacityFrames;

            const uint32_t firstFrames =
                std::min(
                    framesToRead,
                    m_capacityFrames - readIndex);

            std::memcpy(
                data,
                m_buffer.data() +
                    static_cast<size_t>(readIndex) *
                    m_bytesPerFrame,
                static_cast<size_t>(firstFrames) *
                m_bytesPerFrame);

            if (firstFrames < framesToRead)
            {
                std::memcpy(
                    static_cast<uint8_t*>(data) +
                        static_cast<size_t>(firstFrames) *
                        m_bytesPerFrame,
                    m_buffer.data(),
                    static_cast<size_t>(framesToRead - firstFrames) *
                    m_bytesPerFrame);
            }

            m_readPosition.fetch_add(
                framesToRead,
                std::memory_order_release);

            return framesToRead;
        }

        uint32_t AvailableFrames() const
        {
            return
                m_writePosition.load(std::memory_order_acquire) -
                m_readPosition.load(std::memory_order_acquire);
        }

        uint32_t CapacityFrames() const
        {
            return m_capacityFrames;
        }

    private:
        const uint32_t m_capacityFrames;
        const uint32_t m_bytesPerFrame;

        std::vector<uint8_t> m_buffer;

        alignas(64)
        std::atomic<uint32_t> m_writePosition{0};

        alignas(64)
        std::atomic<uint32_t> m_readPosition{0};
    };
}

int ZelvikNative_GetVersion()
{
    return 1;
}

void* ZelvikNative_AudioBuffer_Create(
    uint32_t capacityFrames,
    uint32_t bytesPerFrame)
{
    if (capacityFrames == 0 || bytesPerFrame == 0)
    {
        return nullptr;
    }

    try
    {
        return new AudioRingBuffer(
            capacityFrames,
            bytesPerFrame);
    }
    catch (...)
    {
        return nullptr;
    }
}

void ZelvikNative_AudioBuffer_Destroy(
    void* handle)
{
    delete static_cast<AudioRingBuffer*>(handle);
}

uint32_t ZelvikNative_AudioBuffer_Write(
    void* handle,
    const void* data,
    uint32_t frameCount)
{
    if (!handle)
    {
        return 0;
    }

    return static_cast<AudioRingBuffer*>(handle)->Write(
        data,
        frameCount);
}

uint32_t ZelvikNative_AudioBuffer_Read(
    void* handle,
    void* data,
    uint32_t frameCount)
{
    if (!handle)
    {
        return 0;
    }

    return static_cast<AudioRingBuffer*>(handle)->Read(
        data,
        frameCount);
}

uint32_t ZelvikNative_AudioBuffer_AvailableFrames(
    void* handle)
{
    if (!handle)
    {
        return 0;
    }

    return static_cast<AudioRingBuffer*>(handle)->AvailableFrames();
}

uint32_t ZelvikNative_AudioBuffer_CapacityFrames(
    void* handle)
{
    if (!handle)
    {
        return 0;
    }

    return static_cast<AudioRingBuffer*>(handle)->CapacityFrames();
}