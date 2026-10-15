#!/usr/bin/env python3
"""Run the pinned Metal cleanup functions against owned and mmap-borrowed storage.

Only Objective-C MTLBuffer release calls and residency-set release are mocked;
the actual C ownership/cleanup bodies are extracted unchanged from the runtime.
Uses the iOS free() branch on Linux/macOS, without requiring an Apple GPU.
"""
import argparse, re, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
s=(a.source/'ggml/src/ggml-metal/ggml-metal.m').read_text()
def body(name):
    start=s.index('static void '+name+'(')
    end=s.index('\n}\n',start)+3
    return s[start:end].replace('[ctx->buffers[i].metal release];','release_metal(ctx->buffers[i].metal);')
mapped=s[s.rindex('static ggml_backend_buffer_t ggml_backend_metal_device_buffer_mapped('):]
mapped=mapped[:mapped.index('\n}\n')]
assert 'mapped_i.free_buffer = ggml_backend_metal_buffer_mapped_free_buffer;' in mapped
assert 'ggml_backend_metal_buffer_type_mapped(), mapped_i, ctx, size' in mapped
shared=s[s.index('static struct ggml_backend_buffer_i ggml_backend_metal_buffer_shared_i'):]
assert 'ggml_backend_metal_buffer_shared_free_buffer' in shared[:shared.index('};')]
code=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/mman.h>
#define TARGET_OS_OSX 0
#define GGML_ASSERT assert
struct ggml_backend_metal_buffer_context {
    int n_buffers; struct {void *metal;} buffers[2]; bool is_shared;
    void *all_data; size_t all_size;
};
struct ggml_backend_buffer {void *context;};
typedef struct ggml_backend_buffer *ggml_backend_buffer_t;
static int releases, residency, storage_frees;
static void *owned_storage;
static void release_metal(void *p) { assert(p); ++releases; }
static void ggml_backend_metal_buffer_rset_free(struct ggml_backend_metal_buffer_context *p) { assert(p); ++residency; }
static void checked_free(void *p) { if(p==owned_storage) ++storage_frees; free(p); }
#define free checked_free
'''+body('ggml_backend_metal_buffer_shared_free_buffer')+body('ggml_backend_metal_buffer_mapped_free_buffer')+r'''
#undef free
int main(void) {
 for(int repeat=0;repeat<100;++repeat) {
    size_t size=16384;
    unsigned char *mapping=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
    assert(mapping!=MAP_FAILED); mapping[4096]=37;
    struct ggml_backend_metal_buffer_context *ctx=calloc(1,sizeof(*ctx));
    ctx->all_data=mapping+4096; ctx->all_size=4096; ctx->is_shared=true; ctx->n_buffers=2;
    ctx->buffers[0].metal=ctx; ctx->buffers[1].metal=ctx;
    struct ggml_backend_buffer buffer={ctx};
    int r=releases, rs=residency;
    ggml_backend_metal_buffer_mapped_free_buffer(&buffer);
    assert(releases==r+2 && residency==rs+1);
    assert(mapping[4096]==37); mapping[4096]=99; assert(mapping[4096]==99);
    assert(munmap(mapping,size)==0);
    ctx=calloc(1,sizeof(*ctx)); owned_storage=malloc(size); assert(owned_storage);
    ctx->all_data=owned_storage; ctx->all_size=size; ctx->is_shared=true;
    buffer.context=ctx; int f=storage_frees;
    ggml_backend_metal_buffer_shared_free_buffer(&buffer);
    assert(storage_frees==f+1); owned_storage=NULL;
 }
 puts("PASS: 100 borrowed-mmap and owned-allocation cleanup cycles; correct dispatch and wrapper cleanup");
}
'''
with tempfile.TemporaryDirectory(prefix='metal-ownership-') as tmp:
    root=Path(tmp); (root/'test.c').write_text(code)
    subprocess.run(['cc','-std=c11','-D_DEFAULT_SOURCE','-fsanitize=address','-g',str(root/'test.c'),'-o',str(root/'test')],check=True)
    subprocess.run([str(root/'test')],check=True)
