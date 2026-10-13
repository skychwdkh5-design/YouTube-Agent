# EP002 Dubai — NASA World of Change URL Audit

Base: 527df67. Source page: https://science.nasa.gov/earth/earth-observatory/world-of-change/dubai/ (12 ASTER frames, Terra).
Official download listing: https://science.nasa.gov/earth/earth-observatory/world-of-change/dubai/all-images/ (captions 'Image of Dubai from [date]', credit 'Earth Observatory').

## Method
1. WebFetch of the WoC page: 12 article-body image URLs with date captions. These are `dynamicimage` display URLs carrying `?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint`, i.e. a 720x480 render request, not native size.
2. WebFetch of the all-images page: for each date, a display URL and a 'Download large image' URL (`content/dam/.../dubai_ast_YYYYMMDD_cyl.jpg`). Dates match page one by one.
3. The URLs are quoted from page text read through a fetch summary tool. The image hosts could not be reached from this session, so no URL was opened, no image was downloaded, and no URL variant was constructed by me. 'cyl' in the filename is NASA's wording; nothing is inferred from it about georeferencing (claim 32 stays UNVERIFIED).

## URL mapping (large image = preferred; page-listed display URL = 720x480 fallback)
| key | caption date | large image URL | display URL (as listed) | status |
|---|---|---|---|---|
| WOC-2000 | 11 Nov 2000 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20001111_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20001111.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2002a | 2 Feb 2002 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20020202_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20020202.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2002b | 16 Oct 2002 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20021016_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20021016.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2003 | 4 Nov 2003 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20031104_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20031104.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2004 | 6 Nov 2004 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20041106_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20041106.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2005 | 24 Oct 2005 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20051024_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20051024.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2006 | 18 Sep 2006 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20060918_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20060918.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2007 | 4 Mar 2007 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20070304_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20070304.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2008 | 17 Nov 2008 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20081117_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20081117.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2009 | 5 Feb 2009 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20090205_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20090205.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2010 | 8 Feb 2010 | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20100208_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20100208.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |
| WOC-2011 | caption 25 Apr 2011; use 2011 only | https://assets.science.nasa.gov/content/dam/science/esd/eo/woc/images/dubai/dubai_ast_20110425_cyl.jpg | https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/woc/images/dubai/dubai_20110425.jpg?w=720&h=480&fit=clip&crop=faces%2Cfocalpoint | URL_KNOWN; access UNVERIFIED; dimensions UNVERIFIED |

## Checks
- Dates: all 12 caption dates match claim 21 and the manifest. The last frame is captioned 25 Apr 2011 (file name 20110425) while the article text says February 2011; the video uses 2011 only.
- Thumbnail check: the large-image links are separate `content/dam` files from the 720x480 display renders; whether they are truly larger is NOT verified because no metadata was read.
- Dimensions and file sizes: not stated by NASA on either page. UNRESOLVED.
- Credit: 'Earth Observatory' (all-images page); ASTER on Terra (WoC text). Reuse: attribute NASA Earth Observatory; NASA's own reuse terms were not read in this task.
- No frame is UNRESOLVED as to URL. Whether each URL serves an image, and which crop works, is unresolved.

## Access restrictions
assets.science.nasa.gov was blocked for curl (403 proxy) and unresolvable by WebFetch earlier in this project. The science.nasa.gov pages were readable. Downloads may need to run from a machine with normal access.
