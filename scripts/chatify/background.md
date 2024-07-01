**⚠ Experimental LLM-enhanced tutorial ⚠**

This notebook includes Neuromatch's experimental [Chatify](https://github.com/ContextLab/chatify) 🤖 functionality. The Chatify notebook extension adds support for a large language model-based "coding tutor" to the materials. The tutor provides automatically generated text to help explain any code cell in this notebook.

Note that using Chatify may cause breaking changes and/or provide incorrect or misleading information. If you wish to proceed by installing and enabling the Chatify extension, you should run the next two code blocks (hidden by default). If you do *not* want to use this experimental version of the Neuromatch materials, please use the [stable](https://deeplearning.neuromatch.io/tutorials/intro.html) materials instead.

To use the Chatify helper, insert the `%%explain` magic command at the start of any code cell and then run it (shift + enter) to access an interface for receiving LLM-based assitance. You can then select different options from the dropdown menus depending on what sort of assitance you want.  To disable Chatify and run the code block as usual, simply delete the `%%explain` command and re-run the cell.

Note that, by default, all of Chatify's responses are generated locally. This often takes several minutes per response.  Once you click the "Submit request" button, just be patient-- stuff is happening even if you can't see it right away!

Thanks for giving Chatify a try! Love it? Hate it? Either way, we'd love to hear from you about your Chatify experience!  Please consider filling out our [brief survey](https://forms.gle/jNq85KVvNwj1JHZV9) to provide feedback and help us make Chatify more awesome!

**Run the next two cells to install and configure Chatify...**