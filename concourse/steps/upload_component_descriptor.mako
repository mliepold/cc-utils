<%def
  name="upload_component_descriptor_step(job_step, indent)",
  filter="indent_func(indent),trim"
>
<%
from makoutil import indent_func
from concourse.steps import step_lib
import concourse.steps.component_descriptor_util as cdu
import gci.componentmodel
import os
import product.v2

component_descriptor_v2_path = os.path.join(
  job_step.input('component_descriptor_dir'),
  cdu.component_descriptor_fname(gci.componentmodel.SchemaVersion.V2),
)
ctf_path = os.path.join(
  job_step.input('component_descriptor_dir'),
  product.v2.CTF_OUT_DIR_NAME,
)

%>

${step_lib('upload_component_descriptor')}

upload_component_descriptor(
  component_descriptor_v2_path='${component_descriptor_v2_path}',
  ctf_path='${ctf_path}',
)

</%def>