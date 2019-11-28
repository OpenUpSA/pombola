<h1>Name Resolution Background</h1>
<h2>Blog post originally on MySociety's internal site</h2>
<div class="entry-content">
		<p>I guess that&nbsp;even people outside the parliaments team are aware that one of the major time sinks for maintaining the People’s Assembly site is dealing with speeches or committee appearances being associated with the wrong people. I’ve started working on updating the versions of SayIt and Django that Pombola uses recently, but we didn’t want to embark on that&nbsp;without thinking a bit about the architecture we want to be heading towards to make the scrapers and name resolution easier to maintain.&nbsp;(“Name resolution” here broadly means taking an ambiguous name from a parliamentary transcript on a particular date and returning the person from an existing dataset we think it’s most likely referring to.)</p>
<p>To be clear, I don’t think we’re going to get to our ideal architecture in one go, but I want to make sure that the changes we make in these upgrades is moving towards that.</p>
<p>I’ve written <a href="https://blogs.mysociety.org/internal/2014/07/23/how-names-are-resolved-by-pombola-scrapers/">a bit about how complex and broken the current system is before</a>, so I won’t recapitulate that here. Instead let’s start with a few properties that we I think that we’d like in the end:</p>
<ol>
<li><strong>The scrapers should be standalone scripts that output structured data</strong>. At the moment the scrapers in the za-hansard &nbsp;repository not only depend on having a database present, they &nbsp;actually depend on Django too. I’d like it if these scrapers did just one thing well – went to the parliament website, fetched documents, and turned them into structured data. (This would make them simpler for other people to hack on, or use to get the data for other purposes; one of the first things Code4SA did when looking at za-hansard was to try to take out the Django dependency to make it easier to work on.)</li>
<li><strong>There should be a name-resolution API which is generically useful for Popolo data.</strong>&nbsp;We discussed in the past <a href="https://github.com/mysociety/popit-api/issues/70">making name resolution one of the unique selling points of PopIt</a>. Even though we’re retiring PopIt, people are still enthusiastic about this – it’s a problem that’s widely known to be hard, and existing services to do it are too difficult to use. Here are some properties I think this should have:
<ul>
<li>The facility for a user to create a new resolver based on Popolo JSON, either by manual upload or periodic automatic imports.</li>
<li>An HTTP-based API where you can provide a messy name and (usually) a date and get back&nbsp;a ranked list likely of matches with a likelihood for each.</li>
<li>Allow you to restrict matches by organization (e.g. if you say ‘organization=Labour Party’ it’ll only find people who were members of the Labour Party on the date in question).</li>
<li>Only require Popolo data as input to set it up.</li>
<li>Have an admin interface to allow you to manually override bad matches. It’s important that the people who can spot mistakes (our partners who know the local politics in a country) can make corrections themselves. So they should be able to say “between [start date] and [end date], ‘Jim Hacker’ refers to ‘James George Hacker MP’, and not [another Jim Hacker]”</li>
</ul>
</li>
<li><strong>It should be simpler to investigate and fix errors in name matching</strong>. At the moment the usual way we investigate a problem in name resolution is literally to single-step through the code that finds a match. Ideally it should be a single click on the site for any administrator to see all the matches that were considered when they spot a bad speech assignment. They should also be able to click through in order&nbsp;to add an exception, or to correct the name data in the database. (This might involve triggering a reparse of the data.)</li>
<li><strong>We should preserve the documents that are scraped and parsed and make them available</strong>. The documents (typically PDFs or word documents) that we scrape and parse have a habit of disappearing from their original location – that makes it much very hard to figure out who it really was who was speaking in the case of any error or confusion. It would be nice to be able to link to our cache of the source documents as well as the original URL.</li>
<li><strong>Our effort should be put into code or services that will be reusable no matter&nbsp;the future of Pombola is</strong>. We don’t <em>precisely</em>&nbsp;know what the future of Pombola looks like, but the plan for a long time has been to externalize much more of its functionality into distinct packages, and there’s an added motivation to do this since we’ve recently been discussing reusing some parts of the codebase to augment “Pombola Simple” static sites.</li>
</ol>
<p>Hopefully the user needs for the first four points here are fairly clear: for developers (including us) it’s&nbsp;way too difficult to fix (or even detect!) scraping errors in People’s Assembly, and we’ve heard from lots of civic tech hackers that they’d be really interested in a name resolution compoment. The user needs for our international partners (e.g. PMG and Mzalendo) are also apparent: they’re frustrated by having to have developer time available from us to be able to fix what look like obvious mistakes to them.</p>
<p>I think that the work I’m doing on the SayIt upgrade at the moment gives us a good opportunity to work towards the second of these goals (a standalone name resolution component), and the others are ones that we should bear in mind in planning in subsequent sprints.</p>
<h3>&nbsp;More about the SayIt upgrade</h3>
<p>We’re still using quite an old version of SayIt in Pombola, which predated its use of django-popolo. (A SayIt speaker now is based on a django-popolo Person using Django’s multi-table inheritance.)</p>
<p>Upgrading the version of SayIt used by People’s Assembly is quite involved—you can see the gory details in the <a href="https://github.com/mysociety/pombola/pull/1951">first of several pull requests</a>—but let’s just consider part of it: a Django application&nbsp;called “popit-resolver”. This application essentially did the following:</p>
<ul>
<li>Took the URL of a PopIt instance,</li>
<li>Fetched all the people data from it,</li>
<li>Indexed as many reasonable variants of each name as it could in Elasticsearch (via Haystack),</li>
<li>Offered a method to retrieve the best match from Elasticsearch for a possibly ambiguous or messy name, such as you might get from a parliamentary transcript.</li>
</ul>
<p>Obviously this would have to change, since we’re retiring PopIt. I decided to fork this and rename it “popolo-name-resolver” and change where it sources its people data from. Instead of going to PopIt, popolo-name-resolver assumes that django-popolo’s models are already populated.</p>
<p>This is nice because:</p>
<ul>
<li>SayIt speakers are directly returned from the name matching. (Well, really it’s a django-popolo Person, but they’re related via multi-table inheritance.)</li>
<li>There’s already a management command that we added to django-popolo to import data from from PopIt export.json, so populating it in that way is easy, if you want to.</li>
<li>Since it’s a Django application we could easily add an API to this, or a user-facing front-end so you can upload your own Popolo data.</li>
<li>If we used django-subdomain-instances to provide multiple sudomains, you could allow third parties to create their own name resolvers which they upload Popolo data to. If people started using this widely for recognizing names in &nbsp;parliamentary or government data, you add an option to search for a name without restricting the instance, and … ta-dah! … you have an awesome API to search for PEPs (<a href="https://en.wikipedia.org/wiki/Politically_exposed_person">Politically Exposed Persons</a>). (Tony told us that&nbsp;at an investigative journalism event that he went to many people were crying out for tools to quickly find people of interest in large data dumps or leaks.)</li>
</ul>
<p>So even though it’s very basic at the moment, I’m hoping that this can be the basis of our name resolution component. The code could do with a lot of work, and the name variants aren’t constructed as smartly as they could be, but it’s a start to work from.</p>
<p>It’s also worth noting that Struan added name resolution to PopIt with a similar strategy (store multiple name variants in Elasticsearch) but that was never merged – we should revisit that work so see how the ideas there could be used to improve popolo-name-resolver.</p>
<h3>Next Steps…</h3>
<h4>… for popolo-name-resolver</h4>
<p>An obvious step after the above is to add an admin interface to popolo-name-resolver to allow overrides for wrong matches of names to people. (This is another part of addressing point 2&nbsp;above.) This can be a slightly more sophisticated version of pombola.hansard’s “alias” system at first.</p>
<h4>… for za-hansard</h4>
<p>One of the&nbsp;next things to focus on is probably point 1: making the za-hansard repository simpler, and its output better structured. (za-hansard is the repository that stores the scrapers for South Africa, it&nbsp;also keeps track of URLs of source documents in Django models.) At the moment the structured data it generates is awkward to navigate (e.g. for committee transcripts the filename is based on an ID stored in the database).</p>
<p>We should store, in predictable filesystem locations, the following:</p>
<ul>
<li>The original document</li>
<li>A parsed version of the original document as structured data (typically JSON or Akoma Ntoso format) with people’s names as they appear in the transcript (i.e. before popolo-name-resolver has been used)</li>
</ul>
<p>A later stage of the pipeline should also generate:</p>
<ul>
<li>A parsed version of the original document as structured data but also with the IDs of speakers returned from popolo-name-resolver.</li>
</ul>
<p>(Some people will prefer one version of the structured data, some the other – it’d be good to provide both, making sure they’re updated when we reparse.)</p>
<p>za-hansard does already cache the data it downloads and generates, but, as mentioned above, it’s confusingly structured and not made available publicly, except on the version we present on the site.</p>
<p>[An alternative to this approach would be to see if we can run the scrapers on morph.io. I haven’t looked into the feasibility of that yet.]</p>
<h3>Next time</h3>
<p>I haven’t discussed here the changes we’d need to make to Pombola to go along with the above, but I’m going to leave that to the next post. That’s going to include:</p>
<ul>
<li>Control of the scrapers from Pombola’s admin (e.g. being able to trigger a reparse of particular documents).</li>
<li>Import of data from the (now less sophisticated) za-hansard, including name matching using popolo-name-resolver.</li>
<li>Adding user interface on Pombola for debugging a name match (goal 3 above).</li>
</ul>
	</div>