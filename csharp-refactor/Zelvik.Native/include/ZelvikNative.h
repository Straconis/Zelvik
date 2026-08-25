#pragma once

#ifdef ZELVIK_NATIVE_EXPORTS
#define ZELVIK_NATIVE_API __declspec(dllexport)
#else
#define ZELVIK_NATIVE_API __declspec(dllimport)
#endif

extern "C"
{
    ZELVIK_NATIVE_API int ZelvikNative_GetVersion();
}