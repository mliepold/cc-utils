import os
import subprocess

import ci.util
import gci.componentmodel
import product.v2

import logging

logger = logger = logging.getLogger('step.upload_component_descriptor')


def upload_component_descriptor(component_descriptor_v2_path, ctf_path):
    have_ctf = os.path.exists(ctf_path)
    have_cd = os.path.exists(component_descriptor_v2_path)

    if not have_ctf ^ have_cd:
        ci.util.fail('exactly one of component-descriptor, or ctf-archive must exist')

    elif have_cd:
        logger.info((f"found CNUDIE-Component-Descriptor at '{component_descriptor_v2_path}'"))
        _upload_component_descriptor_v2(component_descriptor_v2_path)

    elif have_ctf:
        logger.info((f"found ctf-archive at '{ctf_path}'"))
        _upload_ctf(ctf_path)


def _upload_component_descriptor_v2(component_descriptor_path):
    component_descriptor_v2 = gci.componentmodel.ComponentDescriptor.from_dict(
        component_descriptor_dict=ci.util.parse_yaml_file(
            component_descriptor_path
        ),
    )

    logger.info(f'publishing CNUDIE-Component-Descriptor at {component_descriptor_path=}')
    product.v2.upload_component_descriptor_v2_to_oci_registry(
        component_descriptor_v2=component_descriptor_v2,
    )


def _upload_ctf(ctf_path):
    logger.info(f'publishing from ctf-archive at {ctf_path=}')
    subprocess.run(
        [
            'component-cli',
            'ctf',
            'push',
            ctf_path,
        ],
        check=True,
        # env=subproc_env,
    )
