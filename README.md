# XfaConvert
A Python library for extracting Xfa from an interactive PDF document and converting it to several formats. 


# Usage
```py
from xfa import Xfa
```

An example of how to read and and convert an Xfa object:

```py
xfa = Xfa("sample_form.pdf") # An Xfa object from the PDF

# Now we can convert the Xfa to a JSON string
json: str = xfa.convert(output = "json") 

```

We can also save the Xfa to disk to another filetype like YAML:

```py
xfa.save(ext = "yaml") # Converts and saves the xfa instance to a yaml file with the filename "sample_form.pdf.yaml"
```

These are the current file types supported for conversion:
```
* CSV
* JSON
* XML
* YAML
```

# License
This project uses the MIT License, feel free to include it in whatever you want.