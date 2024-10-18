<script lang="ts">
	import QuestionIcon from '$lib/components/ui/icons/question-icon.svelte';
	import Markdown from '@magidoc/plugin-svelte-marked';
</script>

<Markdown
	source={`
# Welcome to Cash Compass!

Looks like you're new here. Let's get you comfortable.

First, you should look for the icon below throughout the app. Clicking on it will open a quick info 
about the item you're looking at. From there you can click through to the full documentation.
  `}
/>
<QuestionIcon />
<Markdown
	source={`
We recommend you get started by creating a category. Categories are used to group your transactions.
  `}
/>
