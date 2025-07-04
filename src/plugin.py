#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright 2015-2024 Kevin B. Hendricks, Stratford Ontario

# This plugin's source code is available under the GNU LGPL Version 2.1 or GNU LGPL Version 3 License.
# See https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html or
# https://www.gnu.org/licenses/lgpl.html for the complete text of the license.

import sys
import os
import tempfile, shutil
import re
import inspect

from accessgui import GUIUpdateFromList
from urllib.parse import unquote
from urllib.parse import urlparse
from PIL import Image
from sigil_bs4 import BeautifulSoup

# define unit separator
_US = chr(31)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

_epubtype_aria_map = {
    "abstract"        : "doc-abstract",
    "acknowledgments" : "doc-acknowledgments",
    "afterword"       : "doc-afterword",
    "appendix"        : "doc-appendix",
    "biblioentry"     : "doc-biblioentry",
    "bibliography"    : "doc-bibliography",
    "biblioref"       : "doc-biblioref",
    "chapter"         : "doc-chapter",
    "colophon"        : "doc-colophon",
    "conclusion"      : "doc-conclusion",
    "cover-image"     : "doc-cover",
    "credit"          : "doc-credit",
    "credits"         : "doc-credits",
    "dedication"      : "doc-dedication",
    "endnote"         : "doc-endnote",
    "endnotes"        : "doc-endnotes",
    "epigraph"        : "doc-epigraph",
    "epilogue"        : "doc-epilogue",
    "errata"          : "doc-errata",
    "figure"          : "figure",
    "footnote"        : "doc-footnote",
    "foreword"        : "doc-foreword",
    "glossary"        : "doc-glossary",
    "glossdef"        : "definition",
    "glossref"        : "doc-glossref",
    "glossterm"       : "term",
    "index"           : "doc-index",
    "introduction"    : "doc-introduction",
    "landmarks"       : "directory",
    "list"            : "list",
    "list-item"       : "listitem",
    "noteref"         : "doc-noteref",
    "notice"          : "doc-notice",
    "page-list"       : "doc-pagelist",
    "pagebreak"       : "doc-pagebreak",
    "part"            : "doc-part",
    "preface"         : "doc-preface",
    "prologue"        : "doc-prologue",
    "pullquote"       : "doc-pullquote",
    "qna"             : "doc-qna",
    "referrer"        : "doc-backlink",
    "subtitle"        : "doc-subtitle",
    "table"           : "table",
    "table-row"       : "row",
    "table-cell"      : "cell",
    "tip"             : "doc-tip",
    "toc"             : "doc-toc",
}

_aria_role_allowed_tags = {
    "doc-abstract"       : ("section"),
    "doc-acknowledgments": ("section"),
    "doc-afterword"      : ("section"),
    "doc-appendix"       : ("section"),
    "doc-biblioentry"    : ("li"),
    "doc-bibliography"   : ("section"),
    "doc-biblioref"      : ("a"),
    "doc-chapter"        : ("section"),
    "doc-colophon"       : ("section"),
    "doc-conclusion"     : ("section"),
    "doc-cover"          : ("img"),
    "doc-credit"         : ("section"),
    "doc-credits"        : ("section"),
    "doc-dedication"     : ("section"),
    "doc-endnote"        : ("li"),
    "doc-endnotes"       : ("section"),
    "doc-epigraph"       : (),
    "doc-epilogue"       : ("section"),
    "doc-errata"         : ("section"),
    "figure"             : (),
    "doc-footnote"       : ("aside","footer","header"),
    "doc-foreword"       : ("section"),
    "doc-glossary"       : ("section"),
    "definition"         : (),
    "doc-glossref"       : ("a"),
    "term"               : (),
    "doc-index"          : ("nav","section"),
    "doc-introduction"   : ("section"),
    "directory"          : ("ol","ul"),
    "list"               : (),
    "listitem"           : (),
    "doc-noteref"        : ("a"),
    "doc-notice"         : ("section"),
    "doc-pagelist"       : ("nav","section"),
    "doc-pagebreak"      : ("hr"),
    "doc-part"           : ("section"),
    "doc-preface"        : ("section"),
    "doc-prologue"       : ("section"),
    "doc-pullquote"      : ("aside","section"),
    "doc-qna"            : ("section"),
    "doc-backlink"       : ("a"),
    "doc-subtitle"       : ("h1","h2","h3","h4","h5","h6"),
    "table"              : (),
    "cell"               : (),
    "row"                : (),
    "doc-tip"            : ("aside"),
    "doc-toc"            : ("nav","section"),
}

# these tags allow all aria roles
# subject to some conditions
# conditions field: (href_allowed, need_alt)
_all_role_tags = {
    "a"          : (False, False),
    "abbr"       : (True, False),
    "address"    : (True, False),
    "b"          : (True, False),
    "bdi"        : (True, False),
    "bdo"        : (True, False),
    "blockquote" : (True, False),
    "br"         : (True, False),
    "canvas"     : (True, False),
    "cite"       : (True, False),
    "code"       : (True, False),
    "del"        : (True, False),
    "dfn"        : (True, False),
    "div"        : (True, False),
    "em"         : (True, False),
    "i"          : (True, False),
    "img"        : (False, True),
    "ins"        : (True, False),
    "kbd"        : (True, False),
    "mark"       : (True, False),
    "output"     : (True, False),
    "p"          : (True, False),
    "pre"        : (True, False),
    "q"          : (True, False),
    "rp"         : (True, False),
    "rt"         : (True, False),
    "ruby"       : (True, False),
    "s"          : (True, False),
    "samp"       : (True, False),
    "small"      : (True, False),
    "span"       : (True, False),
    "strong"     : (True, False),
    "sub"        : (True, False),
    "sup"        : (True, False),
    "table"      : (True, False),
    "tbody"      : (True, False),
    "td"         : (True, False),
    "tfoot"      : (True, False),
    "thead"      : (True, False),
    "th"         : (True, False),
    "tr"         : (True, False),
    "time"       : (True, False),
    "u"          : (True, False),
    "var"        : (True, False),
    "wbr"        : (True, False)
}

# epub 3.2 and aria rules makes this quite a mess
def _role_from_etype(etype, tname, has_href, has_alt):
    # first get role for epub type from map
    role = _epubtype_aria_map.get(etype, None)
    if role is None:
        return role
    # a possible role exists, check if allowed
    allowed = False
    # check if role would be in a tag that allows all roles
    # subject to conditions
    if tname in _all_role_tags:
        allowed = True
        (href_allowed, need_alt) = _all_role_tags[tname]
        if not href_allowed and has_href:
            allowed = False
        if need_alt and not has_alt:
            allowed = False
    if allowed:
        return role
    # still need to check for specifc additions/exceptions
    if role in _aria_role_allowed_tags:
        tagset = _aria_role_allowed_tags[role]
        if tname in tagset:
            return role
    return None

_USER_HOME = os.path.expanduser("~")

# default

# extract base language from language code
def baselang(lang):
    if len(lang) > 3:
        if lang[2:3] in "-_":
            return lang[0:2]
    return None

def parse_xmpxml_for_alttext(xmpxml):
    xmpmeta = BeautifulSoup(xmpxml, 'xml')
    alt_dict = {}
    if xmpmeta:
        node = xmpmeta.find('AltTextAccessibility')
        if node:
            for element in node.find_all('li'):
                lang = element.get('xml:lang', 'x-default')
                alt_dict[lang] = element.text
                lg = baselang(lang)
                if lg:
                    alt_dict[lg] = element.txt
    return alt_dict

# extract top level desc text from svg
def parse_svgxml_for_desc(svgxml):
    svgsoup = BeautifulSoup(svgxml, 'xml')
    desc = ""
    if svgsoup:
        node = svgsoup.find('desc')
        if node:
            desc = node.text
    return desc

# extract alt text from image metadata
def get_image_metadata_alttext(imgpath, tgtlang):
    xmpxml = None
    description = ""
    # handle svg as special case since Pillow barfs on it
    if imgpath.lower().endswith('.svg'):
        svgxml=""
        with open(imgpath, 'rb') as f:
            svgxml = f.read().decode('utf-8')
        description = parse_svgxml_for_desc(svgxml)
        return description
    with Image.open(imgpath) as im:
        if im.format == 'WebP':
            if "xmp" in im.info:
               xmpxml = im.info["xmp"]
        if im.format == 'PNG':
            if "XML:com.adobe.xmp" in im.info:
                xmpxml = im.info["XML:com.adobe.xmp"]
        if im.format == 'TIFF':
            if 700 in im.tag_v2:
                xmpxml = im.tag_v2[700]
        if im.format == 'JPEG':
            for segment, content in im.applist:
                if segment == "APP1":
                    marker, xmp_tags = content.split(b"\x00")[:2]
                    if marker == b"http://ns.adobe.com/xap/1.0/":
                        xmpxml = xmp_tags
                        break
        exif = im.getexif()
        # 270 = ImageDescription
        if exif and 270 in exif:
            description = exif[270]
    if not xmpxml:
        return description
    alt_dict = parse_xmpxml_for_alttext(xmpxml)
    # first try full language code match
    if tgtlang in alt_dict:
        return alt_dict[tgtlang]
     # next try base language code match
    lg = baselang(tgtlang)
    if lg and lg in alt_dict:
        return alt_dict[lg]
    # use default
    if 'x-default' in alt_dict:
        return alt_dict['x-default']
    # otherwise fall back to exif image description
    return description

# encode strings for xml
def xmlencode(data):
    if data is None:
        return ''
    newdata = data
    newdata = newdata.replace('&', '&amp;')
    newdata = newdata.replace('<', '&lt;')
    newdata = newdata.replace('>', '&gt;')
    newdata = newdata.replace('"', '&quot;')
    return newdata

# decode xml encoded strings
def xmldecode(data):
    if data is None:
        return ''
    newdata = data
    newdata = newdata.replace('&quot;', '"')
    newdata = newdata.replace('&gt;', '>')
    newdata = newdata.replace('&lt;', '<')
    newdata = newdata.replace('&amp;', '&')
    return newdata

whitespace_re = re.compile("\s+")

# handle possible space delimtied multiple attribute values
def parse_attribute(avalue):
    vals = []
    if avalue is None:
        return vals
    val = avalue.strip()
    if " " in val:
        vals = whitespace_re.split(val)
    else:
        if val != "":
            vals.append(val)
    return vals

# the plugin entry point
def run(bk):

    if bk.launcher_version() < 20210430:
        print("Error: Access-Aide requires a newer version of Sigil >= 1.60")
        return 1
    
    epubversion = bk.epub_version()
    E3 = epubversion.startswith("3")
    print("Processing an epub with version: ", epubversion)

    # get users preferences and set defaults for width of images in gui (in pixels)
    prefs = bk.getPrefs()
    prefs.defaults['basewidth'] = 500

    # before anything check to verify accessibilility schema criteria are met
    # no video or audio files, no javascript, no mathml
    add_accessibility_metadata = True
    for mid, href, mime in bk.media_iter():
        if mime.startswith('audio') or mime.startswith('video'):
            add_accessibility_metadata = False

    # Assume no mathml or javascript in epub2 for the time being until a real
    # test can be determined by walking all of the xhtml files.
    # For E3 we can use the manifest properties
    navid = None
    navfilename = None
    navbookpath = None
    if E3:
        for mid, href, mtype, mprops, fallback, moverlay in bk.manifest_epub3_iter():
            if mprops is not None and "mathml" in mprops:
                add_accessibility_metadata = False
            if mprops is not None and "scripted" in mprops:
                add_accessibility_metadata = False
            if mprops is not None and "nav" in mprops:
                navid = mid
                urlobj = urlparse(href)
                path = unquote(urlobj.path)
                navfilename = os.path.basename(path)
                navbookpath = bk.id_to_bookpath(navid)
        if navid is None:
            print("Error: nav property missing from the opf manifest propertiese")
            return -1

    if not add_accessibility_metadata: 
        print("Warning: accessibility metadata will not be added due to use of video, audio, mathml, or javascript") 

    # find primary language from first dc:language tag
    # and update metadata to include the accessibility metadata
    if add_accessibility_metadata:
        print("\nUpdating the OPF with accessibility schema")
    plang = None
    res = []
    has_access_meta = False
    qp = bk.qp
    metaxml = bk.getmetadataxml()
    qp.setContent(metaxml)
    for text, tagprefix, tagname, tagtype, tagattr in qp.parse_iter():
        if text is not None:
            res.append(text)
            if tagprefix.endswith("dc:language"):
                if plang is None:
                    plang = text
                    # if "-" in text:
                    #     plang, region = text.split("-")
        else:
            if tagname == "meta" and tagtype == "begin":
                if "property" in tagattr:
                    prop = tagattr["property"]
                    if prop.startswith("schema:access"):
                        has_access_meta = True
                if "name" in tagattr:
                    name = tagattr["name"]
                    if name.startswith("schema:access"):
                        has_access_meta = True
            if tagname == "metadata" and tagtype == "end":
                # insert accessibility metadata if needed (assumes schema:accessModeSufficient="textual")
                # which is why we abort if audio or video used, javascript, mathml
                if E3 and not has_access_meta and add_accessibility_metadata:
                    res.append('<meta property="schema:accessibilitySummary">This publication conforms to WCAG 2.1 AA.</meta>\n')
                    res.append('<meta property="schema:accessMode">textual</meta>\n')
                    res.append('<meta property="schema:accessMode">visual</meta>\n')
                    res.append('<meta property="schema:accessModeSufficient">textual</meta>\n')
                    res.append('<meta property="schema:accessibilityFeature">structuralNavigation</meta>\n')
                    res.append('<meta property="schema:accessibilityHazard">none</meta>\n')
                if not E3 and not has_access_meta and add_accessibility_metadata:
                    res.append('<meta name="schema:accessibilitySummary" content="This publication conforms to WCAG 2.1 AA."/>\n')
                    res.append('<meta name="schema:accessMode" content="textual"/>\n')
                    res.append('<meta name="schema:accessModeSufficient" content="textual"/>\n')
                    res.append('<meta name="schema:accessibilityFeature" content="structuralNavigation"/>\n')
                    res.append('<meta name="schema:accessibilityHazard" content="none"/>\n')
            res.append(qp.tag_info_to_xml(tagname, tagtype, tagattr))
    metaxml = "".join(res)
    bk.setmetadataxml(metaxml)

    if plang is None:
        print("Error: at least one dc:language must be specified in the opf")
        return -1

    # // update the package tag to include xml:lang attribute if missing but epub3 only
    if E3:
        pkg_tag = bk.getpackagetag()
        qp = bk.qp
        qp.setContent(pkg_tag)
        res = []
        for text, tagprefix, tagname, tagtype, tagattr in qp.parse_iter():
            if text is not None:
                res.append(text)
            else:
                if tagname == "package" and tagtype == "begin":
                    if "xml:lang" not in tagattr:
                        tagattr["xml:lang"] = plang
                res.append(qp.tag_info_to_xml(tagname, tagtype, tagattr))
        pkg_tag = "".join(res)
        bk.setpackagetag(pkg_tag)

    # epub3 - collect titlemap and etypemap from the nav (key is file bookpath)
    # epub2 - collect titlemap from the ncx (key is file bookpath)
    titlemap = {}
    etypemap = {}
    if E3:
        titlemap, etypemap = parse_nav(bk, navid, navbookpath)
    else:
        tocid = bk.gettocid()
        ncxbookpath = bk.id_to_bookpath(tocid)
        titlemap = parse_ncx(bk, tocid, ncxbookpath)

    # now process every xhtml file (including the nav for E3)
    # adding primary language to html tag, setting the title,
    # and building up a list of image links so that alt attributes 
    # can be more easily added by the ebook developer.
    # and for E3 adding known nav landmark semantics epub:types 
    print("\nProcessing all xhtml files to add accessibility features")
    imglst = []
    for mid, href in bk.text_iter():
        bookpath = bk.id_to_bookpath(mid)
    
        print("   ... updating: ", bookpath, " with manifest id: ", mid)
        xhtmldata, ilst = convert_xhtml(bk, mid, bookpath, plang, titlemap, etypemap, E3)
        bk.writefile(mid, xhtmldata)
        if len(ilst) > 0:
            imglst.extend(ilst)

    # allow user to update alt info for each image tag
    print("\nBuilding a GUI to speed image alt attribute updates")

    # first prevent unsafe access of any files within Sigil 
    # by creating a temporary copy of each image in temp_dir
    # and build up database of bookpath to mimetype
    imgmime = {}
    temp_dir = tempfile.mkdtemp()
    for mid, href, mime in bk.image_iter():
        imgdata = bk.readfile(mid)
        bookpath = bk.id_to_bookpath(mid)
        if mime == "image/svg+xml":
            imgdata = imgdata.encode('utf-8')
        filepath = os.path.join(temp_dir, bookpath.replace("/",os.sep))
        imgmime[bookpath] = mime
        destdir = os.path.dirname(filepath)
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        with open(filepath, "wb") as f:
            f.write(imgdata)


    # now build a list of images and current alt text to pass to the gui
    altlist = []
    for (mid, bookpath, imgcnt, imgsrc, imgbookpath, alttext) in imglst:
        print("   ... ", bookpath, " #", imgcnt, " src:", imgsrc, " alt text:", alttext)
        imgpath = os.path.join(temp_dir, imgbookpath.replace("/",os.sep))
        if not alttext or alttext=='':
            alttext = get_image_metadata_alttext(imgpath, plang)
        alttxt = xmldecode(alttext)
        mime = imgmime[imgbookpath]
        key = imgbookpath + _US + bookpath + _US + str(imgcnt)
        altlist.append([imgpath, imgbookpath, mime, key, alttxt])

    # Allow the User to Change Any alt text strings they desire
    basewidth = prefs['basewidth']
    naltdict = None
    if len(altlist) > 0:
       naltdict = GUIUpdateFromList(altlist, basewidth)

    # done with temp folder so clean up after yourself
    shutil.rmtree(temp_dir)

    if naltdict:
        # process results of alt text gui updates and update the actual xhtml
        print("\n\nUpdating any changed alt attributes for img tags")
        for mid, bookpath, imgcnt, imgsrc, imgbookpath, alttext in imglst:
            key = imgbookpath + _US + bookpath + _US + str(imgcnt)
            altnew = naltdict[key]
            if alttext != altnew:
                print("    ... alt text needs to be updated in: ", bookpath, imgsrc, altnew)
                data = bk.readfile(mid)
                data = update_alt_text(bk, data, imgcnt, imgsrc, altnew)
                bk.writefile(mid, data)
    
    print("Updating Complete")
    bk.savePrefs(prefs)

    # Setting the proper Return value is important.
    # 0 - means success
    # anything else means failure
    return 0
 

# parse the nav, building up a list of first toc titles for each new xhtml file
# to use as html head title tags, also parse the first h1 tag to get a potential 
# title for the nav file itself
# and parse the landmarks to collect epub:type semantics set on files and fragments
# returns the dictionary of titles by bookpath and dictionary of epub:type landmarks
def parse_nav(bk, navid, navbookpath):
    print("\nParsing the nav to collect landmark epub:type info and titles for each xhtml file")
    nav_base = "OEBPS/Text"
    if bk.launcher_version() >= 20190927:
        nav_base = bk.get_startingdir(navbookpath)
    titlemap = {}
    etypemap = {}
    qp = bk.qp
    qp.setContent(bk.readfile(navid))
    in_toc = False
    in_lms = False
    getlabel = False
    navtitle = None
    tochref = None
    prevbookpath = ""
    for text, tagprefix, tagname, tagtype, tagattr in qp.parse_iter():
        if text is None:
            if tagname == "nav" and tagtype == "begin":
                if tagattr is not None and "epub:type" in tagattr:
                    in_toc = tagattr["epub:type"] == "toc"
                    in_lms = tagattr["epub:type"] == "landmarks"
            if in_toc and tagname == "a" and tagtype == "begin":
                if tagattr is not None and "href" in tagattr:
                    tochref = tagattr["href"]
                    getlabel = True
            if in_lms and tagname == "a" and tagtype == "begin":
                if tagattr is not None and "href" in tagattr:
                    lmhref = tagattr["href"]
                    if "epub:type" in tagattr:
                        etype = tagattr["epub:type"]
                        urlobj = urlparse(lmhref)
                        apath = unquote(urlobj.path)
                        filename = os.path.basename(apath)
                        bookpath = "OEBPS/Text/" + filename
                        if bk.launcher_version() >= 20190927:
                           bookpath = bk.build_bookpath(apath, nav_base)
                        fragment = urlobj.fragment
                        if fragment != '':
                            etypemap[bookpath] = ("id", fragment, etype)
                        # else:
                            # Arrgghhh! - epub:type tags on body tags 
                            # are now "strongly discouraged"
                            # etypemap[bookpath] = ("body", '', etype)
        else:
            if navtitle is None and tagprefix.endswith("h1"):
                navtitle = text
                titlemap[navbookpath] = navtitle
            if in_toc and getlabel:
                if tochref is not None:
                    urlobj = urlparse(tochref)
                    apath = unquote(urlobj.path)
                    filename = os.path.basename(apath)
                    bookpath = "OEBPS/Text/" + filename;
                    if bk.launcher_version() >= 20190927:
                        bookpath = bk.build_bookpath(apath, nav_base)
                    if bookpath != prevbookpath:
                        titlemap[bookpath] = text
                    prevbookpath = bookpath
                tochref = None
                getlabel = False

    return titlemap, etypemap


# parse the current toc.ncx to create a titlemap of bookpath to nav label
def parse_ncx(bk, tocid, ncxbookpath):
    ncx_base = "OEBPS"
    if bk.launcher_version() >= 20190927:
        ncx_base = bk.get_startingdir(ncxbookpath)
    ncxdata = bk.readfile(tocid)
    bk.qp.setContent(ncxdata)
    titlemap = {}
    navlable = None
    skip_if_newline = False
    lvl = 0
    prevbookpath = ""
    for txt, tp, tname, ttype, tattr in bk.qp.parse_iter():
        if txt is not None:
            if tp.endswith('.navpoint.navlabel.text'):
                navlabel = txt.strip()
        else:            
            if tname == "content" and tattr is not None and "src" in tattr and tp.endswith("navpoint"):
                href =  tattr["src"]
                urlobj = urlparse(href)
                apath = unquote(urlobj.path)
                filename = os.path.basename(apath)
                bookpath = "OEBPS/Text/" + filename
                if bk.launcher_version() >= 20190927:
                    bookpath = bk.build_bookpath(apath, ncx_base)
                if bookpath != prevbookpath:
                    titlemap[bookpath] = navlabel
                prevbookpath = bookpath
                navlabel = None
    return titlemap


# convert xhtml to be more Accessibility friendly
#  - add lang and xml:lang to html tag attributes
#  - add title info to head title tag
#  - collect info on image use and contents of related alt attributes
#  - add known epub:type semantics from nav landmarks to body tag or tag with "fragment" 
#  - add aria role attributes to complement existing epub:type attributes
# returns updated xhtml and list of lists for images (manifest_id, bookpath, image_count, image_src, alt_text)
def convert_xhtml(bk, mid, bookpath, plang, titlemap, etypemap, E3):
    res = []
    #parse the xhtml, converting on the fly to update it
    qp = bk.qp
    qp.setContent(bk.readfile(mid))
    maintitle = None
    loctype = ""
    fragment = ""
    etype = ""
    if bookpath in etypemap:
        (loctype, fragment, etype) = etypemap[bookpath] 
    imgcnt = 0
    imglst = []
    start_dir = bk.get_startingdir(bookpath)
    
    for text, tprefix, tname, ttype, tattr in qp.parse_iter():
        # bug in quickparser does not properly trim attribute names
        if tattr:
            nattr = {}
            for attname, attval in tattr.items():
                attname = attname.strip(' \v\t\n\r\f')
                nattr[attname] = attval
            tattr.clear()
            tattr = nattr
        if text is not None:
            # get any existing title in head, ignore whitespace
            if "head" in tprefix and tprefix.endswith("title"):
                if text.strip() != "":
                    maintitle = text
            res.append(text)
        else:
            # add missing epub:type for nav landmarks that point to fragments
            if E3 and loctype == "id" and ttype in ("single", "begin"):
                if "id" in tattr:
                    id = tattr["id"]
                    if id == fragment:
                        # handle epub:type possible multiple attribute values
                        vals = parse_attribute(tattr.get("epub:type",""))
                        if etype not in vals:
                            vals.append(etype)
                            tattr["epub:type"] = " ".join(vals)

            # This has been "strongly discouraged" so disabling it

            # add missing epub:type for nav landmarks that have no fragments
            # if E3 and loctype == "body" and tname == "body" and ttype == "begin":
            #     # handle epub:type possible multiple attribute values
            #     vals = parse_attribute(tattr.get("epub:type",""))
            #     if etype not in vals:
            #         vals.append(etype)
            #         tattr["epub:type"] = " ".join(vals)

            # add primary language attributes to html tag
            if tname == "html" and ttype=="begin":
                tattr["lang"] = plang
                tattr["xml:lang"] = plang

            # add missing alt text attributes on img tags
            # build up list of img links and current alt text
            if tname == "img" and ttype in ("single", "begin"):
                imgcnt += 1
                alttext = tattr.get("alt", "")
                tattr["alt"] = alttext
                imgsrc = tattr.get("src","")
                urlobj = urlparse(imgsrc)
                apath = unquote(urlobj.path)
                imgbookpath = bk.build_bookpath(apath, start_dir)
                imglst.append((mid, bookpath, imgcnt, imgsrc, imgbookpath, alttext)) 

            # build add any aria roles you know based on epub:type attributes
            # handle multiple epub:type attribute values
            # handle multiple aria role attribute values
            if E3:
                if ttype in ["begin", "single"] and "epub:type" in tattr:
                    evals = parse_attribute(tattr["epub:type"])
                    rvals = parse_attribute(tattr.get("role",""))
                    has_href = "href" in tattr
                    has_alt = "alt" in tattr
                    for ept in evals:
                        ariarole = _role_from_etype(ept, tname, has_href, has_alt)
                        if ariarole is not None:
                            if ariarole not in rvals:
                                rvals.append(ariarole)
                    # multiple aria roles are discouraged only first
                    # will be used
                    if len(rvals) > 0:
                        tattr["role"] = " ".join(rvals)

            # inject any missing titles if possible
            if tname == "title" and ttype == "end" and "head" in tprefix:
                if maintitle is None:
                    res.append(titlemap.get(bookpath,""))

            # inject any missing titles in self closed title tags  if needed
            if tname == "title" and ttype == "single" and "head" in tprefix:
                ttype = "begin"
                res.append(qp.tag_info_to_xml(tname, ttype, tattr))
                res.append(titlemap.get(bookpath,""))
                tattr = {}
                ttype = "end"

            # work around quickparser serialization bug in Sigil 1.4.3 and earlier
            if bk.launcher_version() < 20210203:
                if ttype == "xmlheader":
                    if tattr and "special" in tattr:
                        tattr["special"] = tattr["special"].strip()
                        
            res.append(qp.tag_info_to_xml(tname, ttype, tattr))

    return "".join(res), imglst


# update xhtml img tag alt attribute text
# returns updated xhtml
def update_alt_text(bk, xhtmldata, imgcnt, imgsrc, alttext):
    res = []
    imgptr = 0
    # parse the xhtml, converting on the fly to update it
    qp = bk.qp
    qp.setContent(xhtmldata)
    for text, tprefix, tname, ttype, tattr in qp.parse_iter():
        if text is not None:
            res.append(text)
        else:
            # add missing alt text attributes on img tags
            # build up list of img links and current alt text
            if tname == "img" and ttype in ("single", "begin"):
                imgptr += 1
                if imgptr == imgcnt:
                    tattr["alt"] = xmlencode(alttext)
            res.append(qp.tag_info_to_xml(tname, ttype, tattr))
    return "".join(res)


def main():
    print("I reached main when I should not have\n")
    return -1
    
if __name__ == "__main__":
    sys.exit(main())

