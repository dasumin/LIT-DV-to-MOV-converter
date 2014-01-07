// YV12Subtract - expansion of AviSynth's Subtract
// YV12Subtract (C) 2003 Kurosu (kurosu@inforezo.org)
// Subtract (C) AviSynth's team

// See legal notice in Interface.cpp and Readme.txt for more information

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA, or visit
// http://www.gnu.org/copyleft/gpl.html .

#ifndef __SUBSTRACT__
#define __SUBSTRACT__

#include "BaseFilter.h"

/*
 * Class for subtracting one clip from another
 */
class YV12Substract : public BaseFilter
{
private:
	PClip			child2;
	int				Y, U, V;
	int				offX, offY, w, h;
	unsigned char	tolerance;
	unsigned char   *LUT;
protected:
    void ProcessY(BYTE *pDst, int nDstPitch, const BYTE *pSrc1, int nSrc1Pitch,
                  const BYTE *pSrc2, int nSrc2Pitch, const BYTE *pSrc3, int nSrc3Pitch);
	void ProcessU(BYTE *pDst, int nDstPitch, const BYTE *pSrc1, int nSrc1Pitch,
                  const BYTE *pSrc2, int nSrc2Pitch, const BYTE *pSrc3, int nSrc3Pitch);
	void ProcessV(BYTE *pDst, int nDstPitch, const BYTE *pSrc1, int nSrc1Pitch,
                  const BYTE *pSrc2, int nSrc2Pitch, const BYTE *pSrc3, int nSrc3Pitch);

void (* SubtractY)(unsigned char *pDst, const unsigned char *pSrc1,
                   const unsigned char *pSrc2, int dstPitch, int src1Pitch,
                   int src2Pitch, int width, int height, unsigned char tol,
                   unsigned char *LUT);
void (* SubtractUV)(unsigned char *pDst, const unsigned char *pSrc1,
                    const unsigned char *pSrc2, int dstPitch, int src1Pitch,
                    int src2Pitch, int width, int height, unsigned char tol,
                    unsigned char *LUT);
public:
	YV12Substract(PClip _child1, PClip _child2, double _tol, bool wideRange, int _X, int _Y,
				  int _w, int _h, int y, int u, int v, bool _mmx, bool _isse, IScriptEnvironment* env);
	PVideoFrame __stdcall GetFrame(int n, IScriptEnvironment* env);
};

#endif