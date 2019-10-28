"""
Code to wrap web fragments with a license.
"""


def wrap_with_license(block, view, frag, context):  # pylint: disable=unused-argument
    """
    In the LMS, display the custom license underneath the XBlock.
    """
    license = getattr(block, "license", None)  # pylint: disable=redefined-builtin
    if license:
        context = {"license": license}
        frag.content += block.runtime.render_template('license_wrapper.html', context)
    return frag
