# SPDX-License-Identifier: MIT
"""Texture codec extracted without GUI from TL-UGC-Editor v0.1.2.
Upstream: https://github.com/PICKLERICK2005/TL-UGC-Editor
Commit: a4b3c45dabd8b145de3adae7e4af1fe226f6847f
The codec below is unmodified. Integration/validation lives in photo_import.py.

MIT License

Copyright (c) 2026 pickle

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import zstandard as zstd

def div_round_up(n:int,d:int)->int: return (n+d-1)//d

def gob_address(x:int, y:int, width_in_gobs:int, bpe:int, block_height:int)->int:
    x_bytes = x * bpe
    gob_addr = ((y // (8 * block_height)) * 512 * block_height * width_in_gobs
                + (x_bytes // 64) * 512 * block_height
                + ((y % (8 * block_height)) // 8) * 512)
    xg = x_bytes % 64
    yg = y % 8
    return (gob_addr
            + ((xg % 64) // 32) * 256
            + ((yg % 8) // 2) * 64
            + ((xg % 32) // 16) * 32
            + (yg % 2) * 16
            + (xg % 16))

def deswizzle_block_linear(data:bytes, width:int, height:int, bpe:int, block_height:int)->bytes:
    width_in_gobs = div_round_up(width*bpe, 64)
    padded_h = div_round_up(height, 8*block_height) * (8*block_height)
    padded_size = width_in_gobs * padded_h * 64
    src = data + b"\x00" * max(0, padded_size-len(data))
    out = bytearray(width*height*bpe)
    for y in range(height):
        for x in range(width):
            s = gob_address(x,y,width_in_gobs,bpe,block_height)
            d = (y*width+x)*bpe
            out[d:d+bpe] = src[s:s+bpe]
    return bytes(out)

def swizzle_block_linear(data:bytes, width:int, height:int, bpe:int, block_height:int)->bytes:
    width_in_gobs = div_round_up(width*bpe,64)
    padded_h = div_round_up(height, 8*block_height)*(8*block_height)
    out = bytearray(width_in_gobs*padded_h*64)
    for y in range(height):
        for x in range(width):
            s=(y*width+x)*bpe
            d=gob_address(x,y,width_in_gobs,bpe,block_height)
            out[d:d+bpe]=data[s:s+bpe]
    return bytes(out)

# ---------------- color helpers ----------------

def rgb565_to_rgb(c:int):
    r=((c>>11)&31)*255//31; g=((c>>5)&63)*255//63; b=(c&31)*255//31
    return r,g,b

def rgb_to_565(r:int,g:int,b:int)->int:
    return ((r*31+127)//255)<<11 | ((g*63+127)//255)<<5 | ((b*31+127)//255)

def srgb_to_lin_u8(v:int)->int:
    f=v/255.0
    l=f/12.92 if f<=0.04045 else ((f+0.055)/1.055)**2.4
    return max(0,min(255,int(l*255+0.5)))

def lin_to_srgb_u8(v:int)->int:
    f=v/255.0
    s=f*12.92 if f<=0.0031308 else 1.055*(f**(1/2.4))-0.055
    return max(0,min(255,int(s*255+0.5)))

def prepare_image(img:Image.Image, w:int, h:int, mode:str='contain')->Image.Image:
    img = img.convert('RGBA')
    if mode in ('stretch', 'fit_stretch'):
        return img.resize((w,h), Image.Resampling.LANCZOS)

    out = Image.new('RGBA', (w,h), (0,0,0,0))
    if mode in ('cover', 'fit_cover'):
        # Fill target while keeping proportions, then center-crop. Good when you want no empty border.
        scale = max(w / img.width, h / img.height)
    else:
        # Default: fit inside target while keeping proportions, with transparent padding.
        scale = min(w / img.width, h / img.height)

    nw = max(1, int(round(img.width * scale)))
    nh = max(1, int(round(img.height * scale)))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (w - nw) // 2
    y = (h - nh) // 2
    out.alpha_composite(resized, (x, y))
    return out

def to_game_linear_rgba(img:Image.Image, w:int, h:int, fit_mode:str='contain')->bytes:
    img = prepare_image(img, w, h, fit_mode)
    raw = bytearray(img.tobytes())
    for i in range(0,len(raw),4):
        raw[i]=srgb_to_lin_u8(raw[i]); raw[i+1]=srgb_to_lin_u8(raw[i+1]); raw[i+2]=srgb_to_lin_u8(raw[i+2])
    return bytes(raw)

def from_game_linear_rgba(raw:bytes)->bytes:
    out=bytearray(raw)
    for i in range(0,len(out),4):
        out[i]=lin_to_srgb_u8(out[i]); out[i+1]=lin_to_srgb_u8(out[i+1]); out[i+2]=lin_to_srgb_u8(out[i+2])
    return bytes(out)

# ---------------- BC1 / BC3 decode + simple encode ----------------

def bc1_decode(blocks:bytes, w:int, h:int)->bytes:
    out=bytearray(w*h*4); pos=0
    for by in range(0,h,4):
        for bx in range(0,w,4):
            c0=int.from_bytes(blocks[pos:pos+2],'little'); c1=int.from_bytes(blocks[pos+2:pos+4],'little')
            bits=int.from_bytes(blocks[pos+4:pos+8],'little'); pos+=8
            r0,g0,b0=rgb565_to_rgb(c0); r1,g1,b1=rgb565_to_rgb(c1)
            if c0>c1:
                pal=[(r0,g0,b0,255),(r1,g1,b1,255),((2*r0+r1)//3,(2*g0+g1)//3,(2*b0+b1)//3,255),((r0+2*r1)//3,(g0+2*g1)//3,(b0+2*b1)//3,255)]
            else:
                pal=[(r0,g0,b0,255),(r1,g1,b1,255),((r0+r1)//2,(g0+g1)//2,(b0+b1)//2,255),(0,0,0,0)]
            for py in range(4):
                for px in range(4):
                    if bx+px>=w or by+py>=h: continue
                    idx=(bits >> (2*(4*py+px))) & 3
                    d=((by+py)*w+(bx+px))*4
                    out[d:d+4]=bytes(pal[idx])
    return bytes(out)

def nearest_rgb(p, pal):
    pr,pg,pb,pa=p
    best=0; bestd=10**12
    for i,(r,g,b,a) in enumerate(pal):
        if pa<128 and a==0: return i
        if a==0: continue
        d=(pr-r)*(pr-r)+(pg-g)*(pg-g)+(pb-b)*(pb-b)
        if d<bestd: bestd=d; best=i
    return best

def block_minmax_rgb(pixels):
    opaque=[p for p in pixels if p[3]>=128]
    if not opaque: return (0,0,0),(0,0,0)
    lo=min(opaque, key=lambda p:p[0]*0.299+p[1]*0.587+p[2]*0.114)
    hi=max(opaque, key=lambda p:p[0]*0.299+p[1]*0.587+p[2]*0.114)
    return hi[:3], lo[:3]

def bc1_encode(rgba:bytes, w:int, h:int)->bytes:
    out=bytearray()
    for by in range(0,h,4):
        for bx in range(0,w,4):
            pix=[]
            for py in range(4):
                for px in range(4):
                    x=min(bx+px,w-1); y=min(by+py,h-1); i=(y*w+x)*4
                    pix.append(tuple(rgba[i:i+4]))
            transparent=any(p[3]<128 for p in pix)
            hi,lo=block_minmax_rgb(pix)
            c0=rgb_to_565(*hi); c1=rgb_to_565(*lo)
            if transparent:
                if c0>c1: c0,c1=c1,c0
            else:
                if c0<=c1: c0,c1=c1,c0
            r0,g0,b0=rgb565_to_rgb(c0); r1,g1,b1=rgb565_to_rgb(c1)
            if c0>c1:
                pal=[(r0,g0,b0,255),(r1,g1,b1,255),((2*r0+r1)//3,(2*g0+g1)//3,(2*b0+b1)//3,255),((r0+2*r1)//3,(g0+2*g1)//3,(b0+2*b1)//3,255)]
            else:
                pal=[(r0,g0,b0,255),(r1,g1,b1,255),((r0+r1)//2,(g0+g1)//2,(b0+b1)//2,255),(0,0,0,0)]
            bits=0
            for n,p in enumerate(pix): bits |= nearest_rgb(p,pal) << (2*n)
            out += c0.to_bytes(2,'little') + c1.to_bytes(2,'little') + bits.to_bytes(4,'little')
    return bytes(out)

def bc3_decode(blocks:bytes, w:int, h:int)->bytes:
    out=bytearray(w*h*4); pos=0
    for by in range(0,h,4):
        for bx in range(0,w,4):
            a0=blocks[pos]; a1=blocks[pos+1]; abits=int.from_bytes(blocks[pos+2:pos+8],'little')
            if a0>a1:
                ap=[a0,a1,(6*a0+1*a1)//7,(5*a0+2*a1)//7,(4*a0+3*a1)//7,(3*a0+4*a1)//7,(2*a0+5*a1)//7,(1*a0+6*a1)//7]
            else:
                ap=[a0,a1,(4*a0+1*a1)//5,(3*a0+2*a1)//5,(2*a0+3*a1)//5,(1*a0+4*a1)//5,0,255]
            colors=bc1_decode(blocks[pos+8:pos+16],4,4); pos+=16
            for py in range(4):
                for px in range(4):
                    if bx+px>=w or by+py>=h: continue
                    ci=(py*4+px)*4; d=((by+py)*w+(bx+px))*4
                    ai=(abits >> (3*(4*py+px))) & 7
                    out[d:d+4]=bytes([colors[ci],colors[ci+1],colors[ci+2],ap[ai]])
    return bytes(out)

def bc3_encode(rgba:bytes, w:int, h:int)->bytes:
    out=bytearray()
    for by in range(0,h,4):
        for bx in range(0,w,4):
            pix=[]
            for py in range(4):
                for px in range(4):
                    x=min(bx+px,w-1); y=min(by+py,h-1); i=(y*w+x)*4
                    pix.append(tuple(rgba[i:i+4]))
            alphas=[p[3] for p in pix]; a0=max(alphas); a1=min(alphas)
            if a0==a1: a0=min(255,a0); a1=max(0,a1-1) if a1 else 0
            ap=[a0,a1,(6*a0+1*a1)//7,(5*a0+2*a1)//7,(4*a0+3*a1)//7,(3*a0+4*a1)//7,(2*a0+5*a1)//7,(1*a0+6*a1)//7]
            abits=0
            for n,a in enumerate(alphas):
                idx=min(range(8), key=lambda k:(a-ap[k])*(a-ap[k]))
                abits |= idx << (3*n)
            colorpix=bytearray()
            for r,g,b,a in pix: colorpix += bytes([r,g,b,255])
            out += bytes([a0,a1]) + abits.to_bytes(6,'little') + bc1_encode(bytes(colorpix),4,4)
    return bytes(out)

# ---------------- file format ----------------

def zstd_decompress(data:bytes)->bytes:
    return zstd.ZstdDecompressor().decompress(data)

def zstd_compress(data:bytes)->bytes:
    return zstd.ZstdCompressor(level=3, write_content_size=True).compress(data)

class Format:
    def __init__(self, kind, px_w, px_h, sw_w, sw_h, bpe, bh, bc=None):
        self.kind=kind; self.px_w=px_w; self.px_h=px_h; self.sw_w=sw_w; self.sw_h=sw_h; self.bpe=bpe; self.bh=bh; self.bc=bc

def infer_format(path:Path, raw:bytes)->Format:
    name=path.name.lower()
    if '.canvas.zs' in name or name.endswith('.canvas.zs'):
        return Format('canvas RGBA8',256,256,256,256,4,16,None)
    if 'thumb' in name:
        return Format('thumb BC3',256,256,64,64,16,8,'bc3')
    if len(raw)==98304 or 'food' in name:
        return Format('ugctex BC1 Food',384,384,96,96,8,16,'bc1')
    return Format('ugctex BC1',512,512,128,128,8,16,'bc1')

def decode_texture(path:Path):
    raw=zstd_decompress(path.read_bytes())
    fmt=infer_format(path,raw)
    linear=deswizzle_block_linear(raw, fmt.sw_w, fmt.sw_h, fmt.bpe, fmt.bh)
    if fmt.bc=='bc1': rgba=bc1_decode(linear,fmt.px_w,fmt.px_h)
    elif fmt.bc=='bc3': rgba=bc3_decode(linear,fmt.px_w,fmt.px_h)
    else: rgba=linear
    rgba=from_game_linear_rgba(rgba)
    return Image.frombytes('RGBA',(fmt.px_w,fmt.px_h),rgba), fmt, raw

def encode_texture(img:Image.Image, fmt:Format, fit_mode:str='contain')->bytes:
    rgba=to_game_linear_rgba(img, fmt.px_w, fmt.px_h, fit_mode)
    if fmt.bc in (None,'bc1'):
        ba=bytearray(rgba)
        for i in range(3,len(ba),4): ba[i]=255 if ba[i]>=128 else 0
        rgba=bytes(ba)
    if fmt.bc=='bc1': linear=bc1_encode(rgba,fmt.px_w,fmt.px_h)
    elif fmt.bc=='bc3': linear=bc3_encode(rgba,fmt.px_w,fmt.px_h)
    else: linear=rgba
    sw=swizzle_block_linear(linear,fmt.sw_w,fmt.sw_h,fmt.bpe,fmt.bh)
    return zstd_compress(sw)
