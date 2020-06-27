# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Backup_Database",
    "author": "Noizirom",
    "version": (0,0,1),
    "blender": (2, 80, 0),
    "location": "View3D > Tools > Backup_Database",
    "description": "Simple Databse to backup blend files",
    "warning": "",
    "wiki_url": "",
    "category": "Objects",
}


import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.app.handlers import persistent

### VERSION ###

bkup_ver = 0
bkup_release = 0
bkup_patch = 1
bkup_version = f"{bkup_ver}.{bkup_release}.{bkup_patch}"

### MESSAGES ###

glob_message = ""
glob_error = ""

def full_timestamp():
    import sqlite3.dbapi2 as S3
    return S3.time.strftime("%c")

### DIRECTORY ###

def temp_file(File):
    import os
    return os.path.join(bpy.app.tempdir, File)

def _dirprint_(File, message):
    print(message)
    with open(File, 'a') as log:
        log.write(message)
        log.write("\n")

def _directories_():
    from os import path, mkdir
    from platform import system
    addondir = path.join(bpy.utils.user_resource('SCRIPTS', "addons"), "Backup_Database")
    startpath = (path.expanduser(f"~/Documents") if system() == 'Darwin' else path.expanduser(f"~\Documents"))
    bkdir = path.join(startpath, "Blend_Backup")
    srcdir = path.join(bkdir, "src")
    dbdir = path.join(srcdir, "BlendBackupDB.db")
    logFile = path.join(srcdir, "Bkup.txt")
    printDBfile = path.join(srcdir, "Bkup_Database.txt")
    manualDB =  (path.join(addondir, "Blend_Backup_Manual.pdf") if path.exists(addondir) else printDBfile)
    _dirprint_(logFile, f"[{full_timestamp()}] [DIRECTORY] Adding {bkdir}, {srcdir}, {dbdir}, {logFile}, {printDBfile}, {manualDB}, {bkdir}")
    if not path.exists(bkdir):
        mkdir(bkdir)
        _dirprint_(logFile, f"[{full_timestamp()}] [DIRECTORY] Created {bkdir}.")
    else:
        _dirprint_(logFile, f"[{full_timestamp()}] [DIRECTORY] {bkdir} Already exists.")
        pass
    if not path.exists(srcdir):
        mkdir(srcdir)
        _dirprint_(logFile, f"[{full_timestamp()}] [DIRECTORY] Created {srcdir}.")
    else:
        _dirprint_(logFile, f"[{full_timestamp()}] [DIRECTORY] {srcdir} Already exists.")
        pass
    return bkdir, srcdir, dbdir, logFile, printDBfile, manualDB

bkdir, srcdir, dbdir, logFile, printDBfile, manualDB = _directories_()

def logprint(message):
    print(message)
    with open(logFile, 'a') as log:
        log.write(message)
        log.write("\n")

### DATABASE ###

class BlendBackupDB:
    """
    A simple interface to the back up Database.
    """
    def __init__(self, File):
        ''' '''
        self.conn = None
        import sqlite3
        try:
            self.file = File
            self.conn = sqlite3.connect(File)#, detect_types=sqlite3.PARSE_DECLTYPES)
            msg = f"[{full_timestamp()}] [DATABASE] : "
            logprint(f'{msg}Connected to {File} Successfully.')
        except (Error, Exception) as error:
            msge = f"[{full_timestamp()}] [ERROR] [DATABASE] : "
            m = f"Failed to Connect to {File}. {error}"
            logprint(f"{msge}{m}")
            # self._errmessage(f"{msge}{m}")
            pass
        ''' '''
        self.cursor = self.conn.cursor()
        self.libs = ["actions",
                    "armatures",
                    "brushes",
                    "cache_files",
                    "cameras",
                    "collections",
                    "curves",
                    "fonts",
                    "grease_pencils",
                    "images",
                    "ipos",
                    "lattices",
                    "lightprobes",
                    "lights",
                    "linestyles",
                    "masks",
                    "materials",
                    "meshes",
                    "metaballs",
                    "movieclips",
                    "node_groups",
                    "objects",
                    "paint_curves",
                    "palettes",
                    "particles",
                    "scenes",
                    "screens",
                    "sounds",
                    "speakers",
                    "texts",
                    "textures",
                    "workspaces",
                    "worlds"]
    ''' '''
    def _close(self):
        msg = f"[{full_timestamp()}] [DATABASE] : "
        self.conn.close()
        logprint(f'{msg} Connection closed Successfully.')
    ''' '''
    def _bkupmessage(self, message):
        global glob_message
        glob_message = message
        bpy.ops.bku.message('INVOKE_DEFAULT')
        logprint(f"[{full_timestamp()}] [MESSAGE] {message}")
        glob_message = ""
    ''' '''
    def _errmessage(self, message):
        global glob_error
        glob_error = message
        bpy.ops.bku.error('INVOKE_DEFAULT')
        logprint(f"[{full_timestamp()}] [ERROR] [MESSAGE] {message}")
        glob_error = ""
    ''' '''
    def _updmessage(self, message):
        global glob_error
        glob_error = message
        bpy.ops.bku.uperror('INVOKE_DEFAULT')
        logprint(f"[{full_timestamp()}] [ERROR] [FILE_EXIST] {message}")
        glob_error = ""
    ''' '''
    def _unique_name(self, base_name, collection=bpy.data.objects):
        import re
        strip_num = lambda bn: bn[0:-4] if (re.search(r'\.(\d{3})$', bn)) else bn
        base_name = strip_num(base_name)
        count = 1
        name = base_name
        #
        while collection.get(name):
            name = "%s.%03d" % (base_name, count)
            count += 1
        return name
    ''' '''
    def _get_file_ver(self, File):
        import struct
        import os.path
        try:
            f = open(File, "rb")
            f.seek(7)
            bitness, endianess, major, minor = struct.unpack("sss2s", f.read(5))
            ver = "{}.{}".format(major.decode(), minor.decode())
            arc = "64 bit" if bitness == b"-" else "32 bit"
            end = "little-endian" if endianess == b"v" else "big-endian"
            return ver, arc, end
        except IOError:
            logprint("Can not read file '{}'".format(File))
        except Exception as e:
            logprint(e)
    ''' '''
    def _get_fileSize(self, File):
        from os import path
        byte_constant = 1024
        bc2 = byte_constant**2
        bc3 = byte_constant**3
        bc4 = byte_constant**4
        byte_data = path.getsize(File)
        return (f"{round((byte_data / byte_constant**4), ndigits=2)} TB" if byte_data >= bc4 else f"{round((byte_data / byte_constant**3), ndigits=2)} GB" if (bc4 > byte_data >= bc3) else f"{round((byte_data / byte_constant**2), ndigits=2)} MB" if (bc3 > byte_data >= bc2) else f"{round((byte_data / byte_constant), ndigits=2)} kb" if (bc2 > byte_data >= byte_constant) else f"{byte_data} bytes")
    ''' '''
    def _get_all_collections(self):
        return {i.name: i for i in bpy.data.collections}, [i.name for i in bpy.data.collections]
    ''' '''
    def _new_collection(self, Name):
        new_coll = bpy.data.collections.new(Name)
        bpy.context.scene.collection.children.link(new_coll)
        return new_coll
    ''' '''
    def _new_subcollection(self, Name, collection):
        new_coll = bpy.data.collections.new(Name)
        bpy.data.collections[collection].children.link(new_coll)
        return new_coll
    ''' '''
    def get_collection(self, Name):
        if bpy.data.collections.get(Name) == None:
            return self._new_collection(Name)
        else:
            return bpy.data.collections.get(Name)
    ''' '''
    def get_subcollection(self, Name, collection):
        if (bpy.data.collections.get(collection) == None) and (bpy.data.collections.get(Name) == None):
            self._new_collection(collection)
            return self._new_subcollection(Name, collection)
        elif bpy.data.collections.get(Name) == None:
            return self._new_subcollection(Name, collection)
        else:
            return bpy.data.collections.get(Name)
    ''' '''
    def _binConvertor(self, File):
        import inspect
        msg = f"[[{full_timestamp()}]] : "
        try:
            with open(File, 'rb') as f:
                blob = f.read()
            return blob
            logprint(f'{msg} Retrieved data from {File} Successfully.')
        except Exception as e:
            m = f"Failed to Retrieve data from {File}. {e}"
            logprint(f"[ERROR] {msg}{m}")
            pass
    ''' '''
    def _to_bin_file(self, File, data):
        import inspect
        msg = f"[[{full_timestamp()}]] : "
        try:
            with open(File, 'wb') as f:
                f.write(data)
                logprint(f'{msg} Wrote data to {File} Successfully.')
        except Exception as e:
            m = f"Failed to Write data to {File}. {e}"
            logprint(f"[ERROR] {msg}{m}")
            pass
    ''' '''
    def _blend_table(self):
        try:
            table = f"""CREATE TABLE IF NOT EXISTS Blend_Files (Id INTEGER PRIMARY KEY AUTOINCREMENT NULL, Name TEXT UNIQUE, Data BLOB, Version TEXT, FileSize TEXT, Architecture TEXT, Date TEXT)"""
            self.cursor.execute(table)
            self.conn.commit()
            logprint(f"[{full_timestamp()}] [TABLE] Created Blend_Files Successfully.")
            self._close()
        except Exception as error:
            msg = f"[TABLE] Failed to Create Blend_Files. {error}"
            logprint(f"[{full_timestamp()}] [ERROR] {msg}")
            pass
    ''' '''
    def _insert_blend(self, Name, data, ver, fsize, arc):
        stamp = full_timestamp()
        msg = f"[{stamp}] : "
        try:
            insert = f"INSERT INTO Blend_Files VALUES (?,?,?,?,?,?,?)"
            self.cursor.execute(insert, (None, Name, data, ver, fsize, arc, stamp))
            self.conn.commit()
            logprint(f"{msg}Inserted Data into [TABLE] Blend_Files Successfully.")
            logprint(f"{msg} | {Name} | {ver} | {fsize} | {arc}")
        except Exception as error:
            message = f"Failed to Insert Data into Blend_Files. {error}"
            logprint(f"{msg} [ERROR] {message}")
            self._errmessage("Failed to Insert Data into Blend_Files.")
            pass
    ''' '''
    def _get_names(self):
        import numpy as np
        msg = f"[{full_timestamp()}] [DATABASE]"
        try:
            sel = f"""SELECT Name FROM Blend_Files """
            self.cursor.execute(sel)
            data = self.cursor.fetchall()
            logprint(f"{msg} Data from [TABLE] Blend_Files Name Successfully.")
            return np.array(data)[:,0].tolist()
        except Exception as error:
            message = f"Failed to Retrieve data from [TABLE] Blend_Files Name. {error}"
            logprint(f"{msg} [ERROR] {message}")
            pass
    ''' '''
    def _get_data(self, Name):
        import inspect
        msg = f"[{full_timestamp()}] [DATABASE]"
        try:
            s = f'SELECT Data FROM Blend_Files WHERE Name = (?)'
            sel = self.cursor.execute(s,(Name,))
            data = sel.fetchone()
            logprint(f"{msg} Data Retrieved from {Name} Successfully.")
            self._close()
            return data[0]
        except Exception as error:
            message = f"Failed to Retrieve Data from {Name}. {error}"
            logprint(f"{msg} [ERROR] {message}")
            self._errmessage(message)
            pass
    ''' '''
    def _load_names_from_attr(self, File, attr):
        msg = f"[{full_timestamp()}] [DATABASE]"
        try:
            with bpy.data.libraries.load(File, link=False) as (data_from, data_to):
                oList = [ob for ob in getattr(data_from, attr)[:]]
            logprint(f"{msg} Data from | {File} | {attr} | Retrieved Successfully.")
            return oList
        except Exception as error:
            logprint(f"{msg} [ERROR] Problem Retrieving Data from | {File} | {attr} |")
    ''' '''
    def _load_from_attr(self, File, attr, collection=bpy.context.collection):
        msg = f"[{full_timestamp()}] [DATABASE]"
        cObs = [i.name for i in collection.objects]
        try:
            with bpy.data.libraries.load(File, link=False) as (data_from, data_to):
                oList = [ob for ob in getattr(data_from, "objects")[:]]
                setattr(data_to, attr, getattr(data_from, attr))
                logprint(f"{msg} {attr} from {File} Loaded Successfully ")
            if (attr == "objects") or (attr == "curves") or (attr == "meshes"):
                for ob in oList:
                    if ob in cObs:
                        logprint(f"{msg} [ERROR] {ob} already in collection!")
                        pass
                    else:
                        collection.objects.link(bpy.data.objects[ob])
                        logprint(f"{msg} {ob} was linked to collection")
        except Exception as error:
            logprint(f"{msg} [ERROR] Error Loading {File}!")
    ''' '''
    def _load_all_attr(self, File, append_workspaces=False, collection=bpy.context.collection):
        msg = f"[{full_timestamp()}] [DATABASE]"
        logprint(f"[{full_timestamp()}] [DATABASE] {File} Loading...")
        cObs = [i.name for i in collection.objects]
        try:
            with bpy.data.libraries.load(File, link=False) as (data_from, data_to):
                logprint(f"{msg} Loading...")
                oList = [ob for ob in getattr(data_from, "objects")[:]]
                container = self.libs.copy()
                container.remove("workspaces")
                attrList = (container if append_workspaces == False else self.libs)
                for i in attrList:
                    setattr(data_to, i, getattr(data_from, i))
            for ob in oList:
                if ob in cObs:
                    pass
                else:
                    collection.objects.link(bpy.data.objects[ob])
            logprint(f"[{full_timestamp()}] [DATABASE] Finished Loading {File}.")
        except Exception as error:
            logprint(f"{msg} [ERROR] Error Loading {File}!")
    ''' '''
    def _load_list_attr(self, File, List, collection=bpy.context.collection):
        with bpy.data.libraries.load(File, link=False) as (data_from, data_to):
            oList = [ob for ob in getattr(data_from, "objects")[:]]
            for i in List:
                setattr(data_to, i, getattr(data_from, i))
        if "objects" in List:
            for ob in oList:
                collection.objects.link(bpy.data.objects[ob])
    ''' '''
    def _load_attr_ob(self, File, attr, ob, collection=bpy.context.collection):
        logprint(f"[{full_timestamp()}] [DATABASE] {ob} Loading...")
        try:
            with bpy.data.libraries.load(File, link=False) as (data_from, data_to):
                if attr == "objects":
                    data_to.objects = [ob]
                    collection.objects.link(bpy.data.objects[ob])
                else:
                    setattr(data_to, attr, [ob])
            logprint(f"[{full_timestamp()}] [DATABASE] Finished Loading {ob}.")
        except Exception as error:
            logprint(f"{msg} [ERROR] Error Loading {ob}!")
    ''' '''
    def _int_timestamp(self):
        import sqlite3.dbapi2 as S3
        return S3.time.time()
    ''' '''
    def _update_data(self, Name, data, ver, fsize, arc):
        stamp = full_timestamp()
        msg = f"[{stamp}] : "
        try:
            logprint(f"[{full_timestamp()}] [DATABASE] Updating Data to {Name}.")
            update = 'UPDATE Blend_Files SET Data = ?, Version = ?, FileSize = ?, Architecture = ?, Date = ? WHERE Name = (?)'
            self.cursor.execute(update, (data, ver, fsize, arc, stamp, Name))
            self.conn.commit()
            logprint(f"[{full_timestamp()}] [DATABASE] Updated {Name} in [TABLE] Blend_Files Data Successfully.")
        except Exception as error:
            message = f"Failed to update data in [TABLE] Blend_Files Data. {error}"
            logprint(f"[{full_timestamp()}] [DATABASE] [ERROR] {message}")
            pass
    ''' '''
    def update_blend(self):
        from os import path, remove
        from bpy import data, ops
        fp = data.filepath
        try:
            if not data.is_saved and (fp != ''):
                msg = f"[{full_timestamp()}] [ERROR] [UPDATE] File not Saved."
                logprint(msg)
                self._errmessage(msg)
                pass
            else:
                pass
        except Exception as error:
            logprint(error)
        finally:
            Name = path.splitext(path.split(fp)[1])[0]
            logprint(f"[{full_timestamp()}] [DATABASE] Update to {Name} Initializing...")
            ops.wm.save_as_mainfile(filepath=fp)
            ver, arc, end = self._get_file_ver(fp)
            fs = self._get_fileSize(fp)
            data = self._binConvertor(fp)
            self._update_data(Name, data, ver, fs, arc)
            logprint(f"[{full_timestamp()}] [UPDATE] {Name} was updated Successfully.")
    ''' '''
    def save_current_blend(self):
        from os import path, remove
        from bpy import data, ops
        fp = data.filepath
        try:
            if not data.is_saved:
                logprint(f"[{full_timestamp()}] [ERROR] [SAVE] File not Saved.")
                self._bkupmessage("Save this file first.")
            elif path.splitext(path.split(fp)[1])[0] in self.list_blends():
                msg = f"Already in Database!!!"
                logprint(f"[{full_timestamp()}] [ERROR] [SAVE] [FILE_EXIST] {msg}")
                self._updmessage(msg)
            else:
                self._bkupmessage(f"Saved {Name} to Database Successfully.")
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [SAVE] {error}")
        finally:
            Name = path.splitext(path.split(fp)[1])[0]
            logprint(f"[{full_timestamp()}] [SAVE] Saving {Name} to Database...")
            ops.wm.save_as_mainfile(filepath=fp)
            ver, arc, end = self._get_file_ver(fp)
            fs = self._get_fileSize(fp)
            data = self._binConvertor(fp)
            self._insert_blend(Name, data, ver, fs, arc)
            logprint(f"[{full_timestamp()}] [SAVE] Saved {Name} to Database Successfully.")
    ''' '''
    def save_from_blend(self, File):
        from os import path
        Name = path.splitext(path.split(File)[1])[0]
        names = self.list_blends()
        try:
            if bpy.context.scene.bknames.bkup_blend_files == (None or ''):
                msg = f"Empty Database!!!"
                logprint(f"[{full_timestamp()}] [ERROR] [DATABASE] [EMPTY] {msg}")
            elif Name in names:
                msg = f"{Name} already in Database!!!"
                logprint(f"[{full_timestamp()}] [ERROR] [MESSAGE] [FILE_EXIST] {msg}")
                self._errmessage(msg)
                pass
            else:
                pass
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [SAVE] {error}")
        finally:
            logprint(f"[{full_timestamp()}] [SAVE] Saving {Name} to Database...")
            ver, arc, end = self._get_file_ver(File)
            fs = self._get_fileSize(File)
            data = self._binConvertor(File)
            self._insert_blend(Name, data, ver, fs, arc)
            message = f"[{full_timestamp()}] [SAVE] Saved {Name} to Database Successfully."
            logprint(message)
            self._bkupmessage(f"Saved {Name} to Database Successfully.")
    ''' '''
    def load_blend_all(self, data, append_workspaces=False, collection=bpy.context.collection):
        from os import remove
        temp = temp_file("Temp.blend")
        try:
            logprint(f"[{full_timestamp()}] [LOAD] Loading {data} from Database...")
            with open(temp, 'wb') as f:
                f.write(self._get_data(data))
                self._load_all_attr(f.name, append_workspaces, collection)
            remove(temp)
            logprint(f"[{full_timestamp()}] [LOAD] Loaded {data} from Database Successfully.")
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [LOAD] Error Loadeding {data}!")
            self._errmessage(error)
    ''' '''
    def load_attr(self, data, attr, collection=bpy.context.collection):
        from os import remove
        temp = temp_file("Temp.blend")
        try:
            logprint(f"[{full_timestamp()}] [LOAD] Loading {attr} from {data}...")
            with open(temp, 'wb') as f:
                f.write(self._get_data(data))
                self._load_from_attr(f.name, attr, collection)
            remove(temp)
            logprint(f"[{full_timestamp()}] [LOAD] Loaded {attr} from {data} Successfully.")
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [LOAD] Error Loadeding {attr} from {data}!")
            self._errmessage(error)
    ''' '''
    def load(self, data, attr, ob, collection=bpy.context.collection):
        from os import remove
        temp = temp_file("Temp.blend")
        try:
            logprint(f"[{full_timestamp()}] [LOAD] Loading {ob} from {data}...")
            with open(temp, 'wb') as f:
                f.write(self._get_data(data))
                self._load_attr_ob(f.name, attr, ob, collection)
            remove(temp)
            logprint(f"[{full_timestamp()}] [LOAD] Loaded {ob} from {data} Successfully.")
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [LOAD] Error Loadeding {ob} from {data}!")
            self._errmessage(error)
    ''' '''
    def blend_ob_names(self, data, attr):
        from os import remove
        temp = temp_file("Temp.blend")
        with open(temp, 'wb') as f:
            f.write(self._get_data(data))
            dList = self._load_names_from_attr(f.name, attr)
        remove(temp)
        return dList
    ''' '''
    def list_blends(self):
        container = self._get_names()
        return container
    ''' '''
    def collection_names(self):
        cd, cl = self._get_all_collections()
        return cl
    ''' '''
    def collection_dict(self):
        cd, cl = self._get_all_collections()
        return cd
    ''' '''
    def save_to_DB(self):
        bpy.ops.bku.blend_save('INVOKE_DEFAULT')
    ''' '''
    def get_table(self):
        from numpy import array
        from sqlite3 import Error
        try:
            gt = 'SELECT Id, Name, Version, FileSize, Architecture FROM Blend_Files'
            sel = self.cursor.execute(gt)
            data = sel.fetchall()
            self.conn.commit()
        except (Error, Exception) as error:
            logprint(f"[{full_timestamp()}] [DATABASE] [ERROR] [TABLE]  Failed to connect to Blend_Files. {error}")
        finally:
            if (self.conn):
                self._close()
                logprint(f"[{full_timestamp()}] [DATABASE] [TABLE] Closed...")
        return array(data)
    ''' '''
    def get_file_data(self, File):
        from numpy import array
        from sqlite3 import Error
        try:
            gt = 'SELECT Version, FileSize, Architecture FROM Blend_Files WHERE Name=(?)'
            sel = self.cursor.execute(gt,(File,))
            data = sel.fetchall()
            self.conn.commit()
            return array(data)[0]
        except (Error, Exception) as error:
            logprint(f"[{full_timestamp()}] [DATABASE] [ERROR] [TABLE] Failed to connect to Blend_Files. {error}")
        finally:
            if (self.conn):
                self._close()
                logprint(f"[{full_timestamp()}] [DATABASE] [TABLE] Closed...")
    ''' '''
    def openFile(self, File):
        from bpy import ops
        from os import path
        temp = path.join(bkdir, f"{File}.blend")
        with open(temp, 'wb') as f:
            f.write(self._get_data(File))
        ops.wm.open_mainfile(filepath=temp)
    ''' '''
    def _delete_from_(self, File):
        dl = 'DELETE FROM Blend_Files WHERE Name = (?)'
        self.cursor.execute(dl,(File,))
        self.conn.commit()
        self._close()

db = BlendBackupDB(dbdir)
db._blend_table()
db._close()

def _launch_(File):
    from os import startfile
    try:
        startfile(File)
        logprint(f"[{full_timestamp()}] [LAUNCH] {File} was Opened.")
    except Exception as error:
        logprint(F"[{full_timestamp()}] [ERROR] error")

def _reload(keep=False):
    from bpy import ops, data
    from os import sys, startfile, remove
    current = data.filepath
    if keep == False:
        startfile(sys.executable)
        remove(current)
        logprint(f"{current} was removed.")
        ops.wm.quit_blender()
    else:
        startfile(sys.executable)
        ops.wm.quit_blender()
        logprint(f"{current} was not removed.")

def _rename_(old, new):
    from os import rename
    rename(r'{}'.format(old), r'{}'.format(new))

def _print_DB_(List):
    import numpy as np
    arr = np.array([np.array(i) for i in List])
    lines = [str(i) for i in arr]
    open(printDBfile, 'w').close()
    with open(printDBfile, 'a') as f:
        for line in lines:
            f.writelines(line)
            f.writelines("\n")
            f.writelines("\n")

def _get_ob_matrix_(File):
    db = BlendBackupDB(dbdir)
    with bpy.data.libraries.load(File, link=False) as (data_from, data_to):
        attrDict = {attr: getattr(data_from, attr)[:] for attr in db.libs}
    db._close()
    for i in attrDict["objects"]:
        if i in attrDict["curves"]:
            attrDict["objects"].remove(i)
            logprint(f"{i} was removed")
        else:
            logprint("clean")
    return attrDict

def _get_count_matrix_(File):
    mat = _get_ob_matrix_(File)
    return {ob: len(mat[ob]) for ob in mat}

def _attr_count_(data, attr):
    from os import remove
    temp = temp_file("Temp.blend")
    with open(temp, 'wb') as f:
        db = BlendBackupDB(dbdir)
        f.write(db._get_data(data))
        count = _get_count_matrix_(f.name)[attr]
        db._close()
    remove(temp)
    return count

### OPERATIONS ###

class OT_BLEND_Save(bpy.types.Operator, ImportHelper):
    """ """
    bl_idname = "bku.blend_save"
    bl_label = "Save Blend File to Database"
    """ """
    filter_glob: bpy.props.StringProperty(
        default='*.blend',
        options={'HIDDEN'}
    )
    """ """
    def execute(self, context):
        import os
        db = BlendBackupDB(dbdir)
        db.save_from_blend(self.filepath)
        db._close()
        return {'FINISHED'}

class OT_BLEND_SaveCurrent(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_save_curr"
    bl_label = "Save Current Blend File to Database"
    """ """
    def execute(self, context):
        """ """
        db = BlendBackupDB(dbdir)
        db.save_current_blend()
        db._close()
        logprint(f"[{full_timestamp()}] [SAVE] Saved {bpy.data.filepath}.")
        return {'FINISHED'}

class OT_BLEND_SaveBool(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_save_bool"
    bl_label = "Save Blend File to Database"
    """ """
    def execute(self, context):
        scn = bpy.context.scene
        if scn.bknames.bkup_save_bool:
            bpy.ops.bku.blend_save_curr('INVOKE_DEFAULT')
        else:
            bpy.ops.bku.blend_save('INVOKE_DEFAULT')
        return {'FINISHED'}

class OT_BLEND_Append(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_append"
    bl_label = "Append from Database"
    """ """
    def execute(self, context):
        scn = bpy.context.scene
        db = BlendBackupDB(dbdir)
        count = (0 if (scn.bknames.bkup_blend_files == (None or '')) else _attr_count_(scn.bknames.bkup_blend_files, scn.bknames.bkup_blend_attr))
        try:
            if not scn.bknames.bkup_append_attr and not scn.bknames.bkup_append_ob:
                db.load_blend_all(scn.bknames.bkup_blend_files, scn.bknames.bkup_append_workspaces)
                db._close()
                ogger.info(f"[{full_timestamp()}] [APPEND] Appended {scn.bknames.bkup_blend_files} Successfully.")
            elif scn.bknames.bkup_append_attr and not scn.bknames.bkup_append_ob:
                if count == 0:
                    logprint(f"[{full_timestamp()}] [ERROR] [APPEND] {scn.bknames.bkup_append_attr} has no items!")
                    db._bkupmessage(f"{bpy.context.scene.bknames.bkup_blend_attr} has no items")
                    db._close()
                    pass
                else:
                    db.load_attr(scn.bknames.bkup_blend_files, scn.bknames.bkup_blend_attr)
                    logprint(f"[{full_timestamp()}] [APPEND] Appended attribute {scn.bknames.bkup_blend_attr} from {scn.bknames.bkup_blend_files} Successfully.")
                    db._close()
            elif scn.bknames.bkup_append_ob:
                if scn.bknames.bkup_blend_ob == (None or ''):
                    logprint(f"[{full_timestamp()}] [ERROR] [APPEND] Something went wrong with Appending!")
                    db._bkupmessage(f"{bpy.context.scene.bknames.bkup_blend_attr} has no items")
                    db._close()
                    pass
                else:
                    db.load(scn.bknames.bkup_blend_files, scn.bknames.bkup_blend_attr, scn.bknames.bkup_blend_ob)
                    logprint(f"[{full_timestamp()}] [APPEND] Appended {scn.bknames.bkup_blend_ob} from {scn.bknames.bkup_blend_attr} in {scn.bknames.bkup_blend_files}.")
                    db._close()
            else:
                logprint(f"[{full_timestamp()}] [ERROR] [APPEND] Something went wrong with Appending!")
                db._close()
                pass
        except (Exception) as error:
            logprint(f"[{full_timestamp()}] [ERROR] [APPEND] {error}")
        return {'FINISHED'}

class OT_BLEND_Load(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_load"
    bl_label = "Load from Database"
    """ """
    def execute(self, context):
        scn = bpy.context.scene
        try:
            db = BlendBackupDB(dbdir)
            db.openFile(scn.bknames.bkup_blend_load)
            logprint(f"[{full_timestamp()}] [LOAD] {scn.bknames.bkup_blend_load} was opened Successfully.")
            db._close()
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [LOAD] Something went wrong! {error}")
        return {'FINISHED'}

class OT_BLEND_Update(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_update"
    bl_label = "Update"
    """ """
    def execute(self, context):
        scn = bpy.context.scene
        try:
            db = BlendBackupDB(dbdir)
            logprint(f"[{full_timestamp()}] [UPDATE] Updating...")
            db.update_blend()
            logprint(f"[{full_timestamp()}] [UPDATE] Update was Successfull.")
            db._close()
            db._bkupmessage(f"Update was Successfull.")
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [UPDATE] Something went wrong! {error}")
        return {'FINISHED'}

class OT_BLEND_Delete(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_delete"
    bl_label = "Delete"
    """ """
    def execute(self, context):
        scn = bpy.context.scene
        File = bpy.context.scene.bknames.bkup_blend_delete
        try:
            db = BlendBackupDB(dbdir)
            if scn.bknames.bkup_delete:
                _reload(keep=scn.bknames.bkup_delete)
                logprint(f"[{full_timestamp()}] [DELETE] Reloading...")
            else:
                db._delete_from_(File)
                logprint(f"[{full_timestamp()}] [DELETE] {scn.bknames.bkup_blend_files} was opened Successfully.")
            db._close()
        except Exception as error:
            logprint(f"[{full_timestamp()}] [ERROR] [DELETE] Something went wrong! {error}")
        return {'FINISHED'}

class OT_BLEND_LaunchLog(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_launch_log"
    bl_label = "Load Log File"
    """ """
    def execute(self, context):
        """ """
        _launch_(logFile)
        logprint(f"[{full_timestamp()}] [LOG] {logFile} loaded Successfully.")
        return {'FINISHED'}

class OT_BLEND_logprint_DB(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_launch_db"
    bl_label = "Load Database File"
    """ """
    def execute(self, context):
        """ """
        db = BlendBackupDB(dbdir)
        data = db.get_table()
        db._close()
        _print_DB_(data)
        _launch_(printDBfile)
        logprint(f"[{full_timestamp()}] [DATABASE] {printDBfile} loaded Successfully.")
        return {'FINISHED'}

class OT_BLEND_Launch_Manual(bpy.types.Operator):
    """ """
    bl_idname = "bku.blend_launch_manual"
    bl_label = "Load Manual"
    """ """
    def execute(self, context):
        """ """
        _launch_(manualDB)
        logprint(f"[{full_timestamp()}] [DATABASE] {manualDB} loaded Successfully.")
        return {'FINISHED'}

### MESSAGE BOX ###

class MessageBox(bpy.types.Operator):
    bl_idname = "bku.message"
    bl_label = "Message"
    
    def execute(self, context):
        logprint(f"[{full_timestamp()}] [MESSAGE] [PRESSED]")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        global glob_message
        logprint(f"[{full_timestamp()}] [MESSAGE] {glob_message}")
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        global glob_message
        self.layout.label(text=glob_message, icon='INFO')

class ErrorBox(bpy.types.Operator):
    bl_idname = "bku.error"
    bl_label = "Error"
    
    def execute(self, context):
        logprint(f"[{full_timestamp()}] [ERROR] [PRESSED]")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        global glob_message
        logprint(f"[{full_timestamp()}] [ERROR] {glob_error}")
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        global glob_error
        self.layout.label(text=glob_error, icon='ERROR')

class UpdateBox(bpy.types.Operator):
    bl_idname = "bku.uperror"
    bl_label = "Do you want update this file?"
    
    def execute(self, context):
        logprint(f"[{full_timestamp()}] [ERROR] [PRESSED]")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        logprint(f"[{full_timestamp()}] [ERROR] Update Invoked.")
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        global glob_error
        self.layout.label(text=glob_error, icon='ERROR')
        box = self.layout.box()
        row = box.row()
        row.operator("bku.blend_update", text="Update File")

### PROPERTIES ###

class NameProp(bpy.types.PropertyGroup):
    def get_file_names(self, context):
        db = BlendBackupDB(dbdir)
        names = db.list_blends()
        items = [(i,i,i) for i in names]
        db._close()
        return items
    
    bkup_blend_files = bpy.props.EnumProperty(
        items=get_file_names,
        description="Append File",
        name="File Names",
        update=get_file_names,
        )
    
    bkup_blend_load = bpy.props.EnumProperty(
        items=get_file_names,
        description="Load File",
        name="",
        update=get_file_names,
        )
    
    bkup_blend_delete = bpy.props.EnumProperty(
        items=get_file_names,
        description="Delete File",
        name="File Names",
        update=get_file_names,
        )
    
    def get_file_attr(self, context):
        db = BlendBackupDB(dbdir)
        items = [(i,i,i) for i in db.libs]
        db._close()
        return items
    
    bkup_blend_attr = bpy.props.EnumProperty(
        items=get_file_attr,
        name="File Attributes",
        update=get_file_attr,
        )
    
    def get_all_obs(self, context):
        scn = bpy.context.scene
        db = BlendBackupDB(dbdir)
        obs = db.blend_ob_names(scn.bknames.bkup_blend_files, scn.bknames.bkup_blend_attr)
        items = [(i,i,i) for i in obs]
        db._close()
        return items
    
    bkup_blend_ob = bpy.props.EnumProperty(
        items=get_all_obs,
        name="File Objects",
        update=get_all_obs,
        )
    
    bkup_append_attr = bpy.props.BoolProperty(
        name="",
        description="Append attribute from Database.",
        default=False,
        )
    
    bkup_append_ob = bpy.props.BoolProperty(
        name="",
        description="Append object from Database.",
        default=False,
        )
    
    bkup_append_workspaces = bpy.props.BoolProperty(
        name="   Append Workspaces",
        description="Append blender workspaces to current file.",
        default=False,
        )
    
    bkup_save_bool = bpy.props.BoolProperty(
        name="Save Current Blend.",
        description="Save the current blend file.",
        default=False,
        )

    bkup_delete = bpy.props.BoolProperty(
        name="Delete Active File.",
        description="Delete the current blend file.",
        default=False,
        )
    
    bkup_time_bool = bpy.props.BoolProperty(
        name=f"Backup | version: {bkup_version}",
        description="Switch between 24 and 12 hour clocks",
        default=False,
        )

### PANELS ###

class VIEW3D_PT_Backup_Panel(bpy.types.Panel):
    bl_label = "Backup Database"
    bl_idname = "OBJECT_PT_backup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = "Backup_Database"

    def draw(self, context):
        from time import asctime, strftime
        scn = bpy.context.scene
        c24 = strftime('%a   %H:%M         %b %d %Y')
        c12 = strftime('%a   %I:%M:%p   %b %d %Y')
        bkup = self.layout.box()
        msg = f"Backup | version: {bkup_version}"
        box = bkup.box()
        box2 = box.box()
        col = box2.column()
        split = col.split(factor=0.475, align=True)
        split.prop(scn.bknames, "bkup_time_bool")
        split = split.split(factor=0.2, align=True)
        split.label(icon='BLENDER',)
        (split.label(text=c24) if scn.bknames.bkup_time_bool else split.label(text=c12))

class VIEW3D_PT_Backup_Save(bpy.types.Panel):
    bl_label = "File Operations"
    bl_idname = "OBJECT_PT_save"
    bl_parent_id = "OBJECT_PT_backup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bkup = self.layout.box()
        (bkup.label(text="Save Current File to Database") if scn.bknames.bkup_save_bool else bkup.label(text="Save Blend File to Database"))
        box = bkup.box()
        row = box.row()
        row.prop(scn.bknames, "bkup_save_bool")
        (None if scn.bknames.bkup_save_bool else row.label(icon='FILE_FOLDER',))
        (row.operator("bku.blend_save_bool", text="Save") if scn.bknames.bkup_save_bool else row.operator("bku.blend_save_bool", text="Save File"))

class VIEW3D_PT_Backup_Append(bpy.types.Panel):
    bl_label = "Append Operations"
    bl_idname = "OBJECT_PT_append"
    bl_parent_id = "OBJECT_PT_backup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bknames = scn.bknames
        bkup = self.layout.box()
        (bkup.label(text="Select Attribute to Append.") if (bknames.bkup_append_attr and not bknames.bkup_append_ob) else bkup.label(text="Select Object to Append.") if bknames.bkup_append_ob else bkup.label(text="Select File to Append."))
        col = bkup.row()
        box = col.box()
        row = box.row()
        row.prop(bknames, "bkup_blend_files")
        row = box.row()
        col = col.box()
        row2 = col.column()
        (row2.label(icon='CHECKBOX_HLT') if bknames.bkup_append_ob else row2.prop(bknames, "bkup_append_attr"))
        (row.prop(bknames, "bkup_blend_attr") if bknames.bkup_append_attr or bknames.bkup_append_ob else row.label(text="Append Attribute"))
        row = box.row()
        col.prop(bknames, "bkup_append_ob")
        row = box.row()
        (row.prop(bknames, "bkup_blend_ob") if bknames.bkup_append_ob else row.label(text="Append Object"))
        row = box.row()
        # 
        (row.label() if bknames.bkup_append_attr or bknames.bkup_append_ob else row.prop(bknames, "bkup_append_workspaces"))
        # 
        (None if not bknames.bkup_append_workspaces or bknames.bkup_append_attr or bknames.bkup_append_ob else row.label(icon='WORKSPACE'))
        row.operator("bku.blend_append", text="Append")

class VIEW3D_PT_Backup_Load(bpy.types.Panel):
    bl_label = "Load Operations"
    bl_idname = "OBJECT_PT_load"
    bl_parent_id = "OBJECT_PT_save"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bkup = self.layout.box()
        bkup.label(text="Load File from Database")
        box = bkup.box()
        row = box.row()
        row.prop(scn.bknames, "bkup_blend_load")
        row.label(icon='FILE',)
        row.operator("bku.blend_load", text="Load File")

class VIEW3D_PT_Backup_Update(bpy.types.Panel):
    bl_label = "Update Operations"
    bl_idname = "OBJECT_PT_update"
    bl_parent_id = "OBJECT_PT_save"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bkup = self.layout.box()
        row = bkup.row()
        col = row.column()
        row = col.row()
        row.label(text="Update Active Files to Database")
        row.label(icon='FILE',)
        row.operator("bku.blend_update", text="Update File")

class VIEW3D_PT_Backup_Delete(bpy.types.Panel):
    bl_label = "Delete Operations"
    bl_idname = "OBJECT_PT_delete"
    bl_parent_id = "OBJECT_PT_save"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bkup = self.layout.box()
        (bkup.label(text="Delete Blend Files from Database") if not scn.bknames.bkup_delete else bkup.label(text="Delete Blend Files from Disk"))
        (bkup.prop(scn.bknames, "bkup_blend_delete") if not scn.bknames.bkup_delete else bkup.label(text="Delete the Active Blend Files from Disk"))
        box = bkup.box()
        row = box.row()
        row.prop(scn.bknames, "bkup_delete")
        (None if scn.bknames.bkup_delete else row.label(icon='FILE',))
        (row.operator("bku.blend_delete", text="Delete") if scn.bknames.bkup_delete else row.operator("bku.blend_delete", text="Delete File"))

class VIEW3D_PT_Backup_Log(bpy.types.Panel):
    bl_label = "Log Operations"
    bl_idname = "OBJECT_PT_Bkup_Log"
    bl_parent_id = "OBJECT_PT_backup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bkup = self.layout.box()
        box = bkup.box()
        row = box.row()
        row.operator("bku.blend_launch_log", text="Print Log")
        row.label(icon='WORDWRAP_ON',)
        row.operator("bku.blend_launch_db", text="Print Database")

class VIEW3D_PT_Backup_Manual(bpy.types.Panel):
    bl_label = "Manual"
    bl_idname = "OBJECT_PT_Bkup_Manual"
    bl_parent_id = "OBJECT_PT_backup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        bkup = self.layout.box()
        box = bkup.box()
        row = box.row()
        row.label(icon='RIGHTARROW',text="Noizirom  |  2020")
        row.label(icon='WORDWRAP_ON',)
        row.operator("bku.blend_launch_manual", text="Load Manual")

class VIEW3D_PT_Backup_Append_Info(bpy.types.Panel):
    bl_label = "File Info"
    bl_idname = "OBJECT_PT_Bkup_append_Info"
    bl_parent_id = "OBJECT_PT_append"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scn = bpy.context.scene
        ver, size, arc = BlendBackupDB(dbdir).get_file_data(scn.bknames.bkup_blend_files)
        bkup = self.layout.box()
        box = bkup.box()
        box2 = box.box()
        col = box2.column()
        split = col.split(factor=0.6, align=True)
        split.label(icon='BLENDER',text="File Version")
        split.label(icon='FILE',)
        split.label(text=ver)
        split = col.split(factor=0.6, align=True)
        split.label(icon='BLENDER',text="File Size")
        split.label(icon='FILE',)
        split.label(text=size)
        split = col.split(factor=0.6, align=True)
        split.label(icon='BLENDER',text="Archictecture")
        split.label(icon='FILE',)
        split.label(text=arc)

### REGISTRY ###

classes = [
    OT_BLEND_Save,
    OT_BLEND_SaveCurrent,
    OT_BLEND_SaveBool,
    OT_BLEND_Append,
    OT_BLEND_Load,
    OT_BLEND_Update,
    OT_BLEND_Delete,
    OT_BLEND_LaunchLog,
    OT_BLEND_logprint_DB,
    OT_BLEND_Launch_Manual,
    MessageBox,
    ErrorBox,
    UpdateBox,
    NameProp,
    VIEW3D_PT_Backup_Panel,
    VIEW3D_PT_Backup_Save,
    VIEW3D_PT_Backup_Append,
    VIEW3D_PT_Backup_Append_Info,
    VIEW3D_PT_Backup_Load,
    VIEW3D_PT_Backup_Update,
    VIEW3D_PT_Backup_Delete,
    VIEW3D_PT_Backup_Log,
    VIEW3D_PT_Backup_Manual,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bknames = bpy.props.PointerProperty(type=NameProp)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bknames

if __name__ == "__main__":
    register()

