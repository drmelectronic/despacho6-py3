#include <Python.h>
#include <unistd.h>
#include <asm/io.h>

static PyObject* readOneByte(PyObject* self, PyObject* args) {
	int ret, portStatus;
	if (!PyArg_ParseTuple(args, "i", &portStatus))
		return NULL;
  if (ioperm(portStatus, 3, 1)){perror("ioperm error");}
  ret = inb(portStatus);   
  if (ioperm(portStatus, 3, 0)){perror("ioperm error");}

	return Py_BuildValue("i", ret);
}

static PyObject* writeOneByte(PyObject* self, PyObject* args) {
	int oneByte, portData;
	if (!PyArg_ParseTuple(args, "ii", &portData, &oneByte)) {
		return NULL;
	}
  if (ioperm(portData, 3, 1)){perror("ioperm error");}
  outb(oneByte,portData);
  if (ioperm(portData, 3, 0)){perror("ioperm error");}
	return Py_None;
}

static PyMethodDef parportMethods[] = {
	{"writeOneByte", writeOneByte, METH_VARARGS,
	 "Writes one byte to the specified address"},
	{"readOneByte", readOneByte, METH_VARARGS,
	 "Reads one byte from the specified address"},
	{NULL, NULL}
};

void initlibparport(void) {
	PyObject *m = 
		Py_InitModule3("libparport", parportMethods, "Read/Write to specified port");
}

