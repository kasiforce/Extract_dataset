SlsReuse: LLM-Powered Serverless Function Reuse
JINFENG WEN, Beijing University of Posts and Telecommunications, China
YUEHAN SUN, Beijing University of Posts and Telecommunications, China
Serverless computing has rapidly emerged as a popular cloud computing paradigm. It enables developers to
implement function-level tasks, i.e., serverless functions, without managing infrastructure. While reducing
operational overhead, it poses challenges, especially for novice developers. Developing functions from scratch
requires adapting to heterogeneous, platform-specific programming styles, making the process time-consuming
and error-prone. Function reuse offers a promising solution to address these challenges. However, research
on serverless computing lacks a dedicated approach for function recommendation. Existing techniques from
traditional contexts remain insufficient due to the semantic gap between task descriptions and heterogeneous
function implementations. Advances in large language models (LLMs), pre-trained on large-scale corpora,
create opportunities to bridge this gap by aligning developer requirements with function semantics.
This paper presents SlsReuse, the first LLM-powered framework for serverless function reuse. Specifically,
SlsReuse first constructs a reusable function repository serving as a foundational knowledge base. Then, it learns
unified semantic-enhanced representations of heterogeneous functions through effective prompt engineering
with few-shot prompting, capturing implicit code intent, target platforms, programming languages, and cloud
services. Finally, given a natural language task query, SlsReuse performs intent-aware discovery combined
with a multi-level pruning strategy and similarity matching. We evaluate SlsReuse on a curated dataset of
110 task queries. Built on ChatGPT-4o, one of the most representative LLMs, SlsReuse achieves Recall@10 of
91.20%, exceeding the state-of-the-art baseline by 24.53 percentage points. Experiments with Llama-3.1 (405B)
Instruct Turbo, Gemini 2.0 Flash, and DeepSeek V3 further confirm the generalization capability of SlsReuse,
yielding consistently strong effectiveness across recent LLMs.
CCS Concepts: • Software and its engineering →Cloud computing; Functionality; • Information
systems →Service discovery and interfaces.
Additional Key Words and Phrases: Serverless computing, Function reuse
ACM Reference Format:
Jinfeng Wen and Yuehan Sun. 2025. SlsReuse: LLM-Powered Serverless Function Reuse. 1, 1 (November 2025),
21 pages. https://doi.org/XXXXXXX.XXXXXXX
1
INTRODUCTION
Serverless computing has rapidly emerged as a prominent paradigm in cloud computing, allowing
developers to concentrate on application business logic while offloading infrastructure provisioning,
scaling, and maintenance to cloud providers [43]. This paradigm has been applied across diverse
domains, including machine learning [42, 49], numerical computing [40], video processing [10, 19],
Internet of Things [26, 52], and big data analytics [17, 21]. Reflecting its increasing adoption and
economic impact, the global serverless computing market is projected to grow from about $19
billion in 2024 to nearly $41 billion by 2028 [9].
Authors’ addresses: Jinfeng Wen, Beijing University of Posts and Telecommunications, Beijing, China, jinfeng.wen@bupt.
edu.cn; Yuehan Sun, Beijing University of Posts and Telecommunications, Beijing, China, thesunyh2019@gmail.com.
Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee
provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and
the full citation on the first page. Copyrights for components of this work owned by others than ACM must be honored.
Abstracting with credit is permitted. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires
prior specific permission and/or a fee. Request permissions from permissions@acm.org.
© 2025 Association for Computing Machinery.
XXXX-XXXX/2025/11-ART $15.00
https://doi.org/XXXXXXX.XXXXXXX
, Vol. 1, No. 1, Article . Publication date: November 2025.
arXiv:2511.17262v1  [cs.SE]  21 Nov 2025


2
Wen et al.
In serverless computing, developers primarily implement event-driven units of execution at the
function granularity, referred to as serverless functions, which interact with diverse cloud services
to accomplish specific tasks. These functions run on fully managed serverless platforms, such as
AWS Lambda [1], Google Cloud Functions [7], and Azure Functions [5], achieving high elasticity
and operational simplicity without direct server management. Despite these advantages, serverless
computing presents considerable barriers, particularly for novice developers [44]. In practice, de-
velopers are required to implement serverless functions from scratch to fulfill specific functionality
requirements. This process is time-consuming, cognitively demanding, and error-prone, owing to
the novel programming paradigm and the style heterogeneity of serverless platforms [44]. Each
platform has its own language support, function interfaces, and service configuration schemes,
forcing developers to consult extensive official documentation to understand details [46]. The
absence of unified standards and comprehensive guidance [44] further steepens the learning curve.
As discussed [8], high-quality tutorials and guides remain scarce, making it difficult for developers
to access reliable information when learning serverless technologies. Consequently, developing
serverless functions from scratch imposes a substantial burden on developers.
One promising solution is to reuse proven serverless functions developed by other developers.
However, in the serverless computing research, the lack of discovery and recommendation mecha-
nisms hinders developers from leveraging reusable functions. Realizing function recommendation
requires addressing several challenges. (1) Lack of reusable function repositories: Unlike microser-
vices, serverless functions currently lack well-structured, dedicated repositories that facilitate
function sharing and reuse. (2) Function code heterogeneity: Serverless function implementations
exhibit significant variation not only in task objectives but also in underlying platforms, program-
ming languages, and cloud service integrations. This heterogeneity hinders consistent interpretation
and comparison. (3) Function and requirement gap: With the new paradigm of serverless computing,
developers generally express task requirements in natural language, which tends to be unstructured,
ambiguous, and imprecise. These descriptions diverge from the terminology and abstractions used
in function implementations, creating a gap that hinders accurate function recommendation.
Existing code recommendation approaches can be broadly categorized into code-to-code and
text-to-code approaches. Code-to-code recommendation methods [28, 31, 34, 41] discover relevant
code snippets based on partial code inputs. While effective in code-centric scenarios, they are
fundamentally misaligned with function reuse driven by text-based task requirements. In contrast,
text-to-code recommendation approaches [11, 12, 20, 22, 38] map natural language descriptions
to code snippets, by treating code as a bag of words and applying keyword-based search [12] or
embedding representation calculation [11, 22, 38]. However, these methods overlook high-level
development goals and fail to capture implicit functional intent, as code is reduced to surface-level
tokens. Moreover, essential programming characteristics in serverless contexts, such as the chosen
serverless platform and cloud service integrations, are not incorporated. These factors are critical
for accurate recommendations and effective function development in serverless computing. Finally,
code tokens used in existing approaches remain misaligned with natural language requirements, as
the two operate at different levels of abstraction. Overall, existing methods lack the useful semantic
modeling and intent alignment required to support effective serverless function reuse.
Recent advancements in Large Language Models (LLMs) offer a prospective direction for ad-
dressing the challenges of serverless function reuse. LLMs have achieved impressive performance
in a variety of software engineering tasks, such as program repair [18], unit test generation [51],
and log parsing [47]. Trained on massive amounts of publicly available data, including source code
and natural language text, LLMs are capable of understanding code implementations, extracting
key information, and inferring task intent. These capabilities make LLMs particularly well-suited
to enable effective serverless function reuse.
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
3
In this paper, we introduce SlsReuse, the first framework for serverless function reuse, which
leverages LLMs to enhance semantic representations. SlsReuse tackles key challenges in serverless
computing, including the lack of reusable functions, heterogeneity in function implementations,
and the semantic gap between task descriptions and serverless functions, through a combination
of structured knowledge extraction, semantic representation, and intent-aware recommendation.
Specifically, SlsReuse first builds a reusable serverless function repository by acquiring functions
from open-sourced benchmarks and applying quality-driven filtering. This repository forms the
foundational base for function recommendations. Second, SlsReuse introduces a semantic represen-
tation paradigm that abstracts function code into a unified structured space, capturing code intent,
target platform, programming languages, and cloud services. This leverages few-shot prompt engi-
neering of LLMs to extract consistent semantic knowledge across heterogeneous implementations.
Finally, given a task query, SlsReuse performs intent-aware function discovery and recommendation.
The query is semantically encoded via LLMs and matched against precomputed function repre-
sentations. A multi-level pruning strategy removes functions with inconsistent attributes, while
similarity-driven matching ranks candidate functions according to alignment with task intent.
To evaluate SlsReuse, we construct a reusable repository of 500 serverless functions spanning
diverse domains and programming languages, as no public dataset is available. We further create
110 task queries to support evaluation. Results show that SlsReuse, powered by ChatGPT-4o (one
of the most representative LLMs known for outstanding performance), achieves Recall@1, @5,
@10, @15, and @20 of 52.13%, 86.13%, 91.20%, 92.67%, and 92.93%, exceeding the state-of-the-
art baseline by 28.80, 35.47, 24.53, 18.67, and 15.60 percentage points, respectively. In terms of
ranking quality measured by Mean Reciprocal Rank (MRR), SlsReuse reaches MRR@1 of 0.5240,
MRR@5 of 0.6547, MRR@10 of 0.6616, MRR@15 of 0.6628, and MRR@20 of 0.6629, yielding relative
improvements of 124.57%, 93.19%, 84.15%, 81.58%, and 80.70% over the state-of-the-art baseline,
respectively. Compared with a customized LLM-based variant method, our multi-level pruning
strategy reduces average recommendation latency by 44.36%. In addition, we test with alternative
LLM backends, including Llama 3.1 (405B) Instruct Turbo, Gemini 2.0 Flash, and DeepSeek V3, to
evaluate generalization. Results confirm the generalization capability of SlsReuse and consistently
high effectiveness across all models.
In summary, this paper makes the following contributions:
• We present SlsReuse, the first framework for serverless function reuse. It introduces a semantic-
enhanced representation that uses LLMs with designed few-shot prompts to extract knowledge.
• We conduct an empirical study on this dataset to evaluate the effectiveness of SlsReuse, showing
that it consistently outperforms state-of-the-art baselines.
2
BACKGROUND ON SERVERLESS COMPUTING
2.1
Difference between Serverless Computing and Other Paradigms
Serverless computing, commonly implemented through Function-as-a-Service (FaaS) serverless
platforms such as AWS Lambda [1], Google Cloud Functions [7], and Azure Functions [5], allows
developers to deploy lightweight, stateless functions. These functions are automatically triggered
by external events, including HTTP requests, message queues, and file uploads. Unlike traditional
monolithic applications, serverless functions are designed to be modular, single-purpose, and
ephemeral, executing within fully managed cloud environments. While both serverless functions
and microservices emphasize modularity and decoupling, they differ fundamentally. Microservices
are long-running, stateful services that expose APIs and maintain dedicated resources. In con-
trast, serverless functions are stateless, event-driven, and invoked on demand, with infrastructure
management fully handled by the serverless platform.
, Vol. 1, No. 1, Article . Publication date: November 2025.


4
Wen et al.
Web 
Request
Scientific 
Computing
Machine
Learning
Image 
Processing
…
Serverless
Platforms
Task Goal
16.
…
17.
var detectResponses = await 
this.RekognitionClient.DetectLabelsAsync(new 
DetectLabelsRequest
18.
{
19.
MinConfidence = MinConfidence,
20.
Image = new Image
21.
{
22.
S3Object = new 
Amazon.Rekognition.Model.S3Object
23.
{
24.
Bucket = record.S3.Bucket.Name,
25.
Name = record.S3.Object.Key
26.
}
27.
}
28.
});
29.
…
30.
}
31.
}
1.
using System;
2.
…
3.
using Amazon.Lambda.S3Event;
4.
using Amazon.Rekognition;
5.
…
6.
using Amazon.S3.Model;
7.
// Assembly attribute to enable the Lambda function's JSON 
input to be converted into a .NET class.
8.
[assembly: 
LambdaSerializer(typeof(Amazon.Lambda.Serialization.
Json.JsonSerializer))]
9.
{
10.
public class Function
11.
{
12.
…
13.
public async Task FunctionHandler(S3Event 
input, ILambdaContext context)
14.
{
15.
//A function for responding to S3 create events.
A Serverless Function Example (Image Processing)
Handler Interface
Languages
Cloud Services
(BaaS)
Fig. 1. The development process and an example of a serverless function.
2.2
Development Process of Serverless Functions
As illustrated in Fig. 1, implementing a serverless function involves encapsulating the intended
task goal (e.g., image processing) in a platform-supported programming language and adhering to
the handler interface defined by the target platform. A key feature of this process is the seamless
integration with cloud services, referred to as Backend-as-a-Service (BaaS). The function can
interact with fully managed services such as object storage (e.g., AWS S3), analysis service (e.g.,
AWS Rekognition), and messaging systems (e.g., Google Pub/Sub). These services are accessed
via SDKs or RESTful APIs, allowing functions to perform operations such as file processing and
database access without re-implementing complex backend functionality. The function finally is
deployed and executed with configuration metadata that specifies its runtime parameters (e.g.,
memory allocation size) and associated event triggers.
Fig. 1 illustrates a serverless function implemented in C# and deployed on AWS Lambda, sourced
from the official AWS GitHub repository [2]. The function is triggered by AWS S3 object creation
events (line 3). Upon invocation through the C# handler interface of AWS Lambda (line 12), it first
verifies whether the uploaded object is an image. If the condition holds, the function calls cloud
service AWS Rekognition to perform image label detection and subsequently appends the detected
labels as metadata tags to the corresponding S3 object (lines 17–29).
While serverless computing abstracts infrastructure management and facilitates rapid, event-
driven function development, it simultaneously introduces complexity in function design and
cloud service integration. Thus, reusing serverless functions is essential to improve development
efficiency, reduce code redundancy, and sustain a maintainable cloud function ecosystem.
3
SLSREUSE: OUR SERVERLESS FUNCTION REUSE FRAMEWORK
We present SlsReuse, a semantic-enhanced framework for serverless function reuse. It addresses
the challenges of recommending heterogeneous functions through three contributions. First, it
alleviates the scarcity of reusable functions by constructing a curated, high-quality repository.
Second, it enables consistent interpretation and comparison by abstracting diverse code into
a unified, semantics-enriched representation space. Third, it narrows the gap between natural
language queries and serverless functions via intent-aware discovery.
Fig. 2 illustrates the overall architecture of SlsReuse, which is organized into two phases: the
preparation phase and the query phase, and encompasses three core components. 1○Function
Repository Construction curates a high-quality repository of serverless functions from open-
source ecosystems (e.g., GitHub). Through quality analysis, it ensures the collected functions are
reliable and reusable, establishing the data foundation for function reuse. 2○Function Represen-
tation Design introduces a novel semantic representation for serverless functions. It employs a
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
5
②Function Representation 
Design
①Function Repository 
Construction
③Function Discovery and 
Recommendation
Input
Task 
Requirement
Intent-Aware 
Recommendation
Quality 
Analysis
Structural
Knowledge
Extraction
Semantic 
Representation
Similarity 
Matching
Output
Repository
Structural
Knowledge
Extraction
Task Description for the LLM query
Intent
Summary
Serverless
Platforms
Cloud
Services
Languages
Guideline Notes
Customized Response
Preparation Phase
Query Phase
Semantic
Representation
ü Intent
Function Code to be Extracted
LLM Prompt Design
Multi-Level 
Pruning ü Platforms
ü Languages
ü Services
Fig. 2. The overview of SlsReuse.
tailored LLM prompt to conduct structural knowledge extraction, abstracting code into a unified
semantic space. The resulting enriched representations enable consistent interpretation and com-
parison across heterogeneous implementations. 3○Function Discovery and Recommendation
aligns developer task requirements with repository functions by transforming natural language
inputs into semantic representations using structural knowledge extraction. It then applies multi-
level pruning and similarity matching to identify and recommend functions with aligned intent.
Next, we describe these components in detail.
3.1
Function Repository Construction
This component is dedicated to constructing a diverse, scalable, and high-quality repository of
serverless functions, which serves as the foundation for function recommendation. To this end,
we curate functions from publicly available and widely adopted open-source benchmarks. These
functions are well-tested and suitable for reuse. Our repository aims to span a wide range of
application domains (e.g., image processing, machine learning, Web services), serverless platforms
(e.g., AWS Lambda, Azure Functions), and programming languages (e.g., Python, JavaScript, C#).
To ensure the functional quality of the collected functions, we design a filtering and normal-
ization process: (1) Trivial function elimination. We apply heuristic-based filtering to exclude
non-substantive or boilerplate functions. Specifically, we remove “Hello World”-style examples,
placeholder code identified through manual inspection, and structurally trivial functions character-
ized by minimal logic or return-only statements. (2) Benchmark script filtering. To isolate reusable
functions from evaluation-related scripts, we further exclude benchmark-specific measurement or
orchestration code that is not part of the serverless function’s core task logic. (3) Function manage-
ment normalization. Each retained serverless function is encapsulated as a uniquely identified unit
containing all relevant code. These units constitute the repository’s fundamental entities.
To accommodate the dynamic and evolving nature of the serverless ecosystem, this component
provides a batch processing interface that supports the incremental integration of new functions
into the repository. This design ensures that the repository remains up to date, comprehensive, and
well-suited for downstream analysis and recommendation.
, Vol. 1, No. 1, Article . Publication date: November 2025.


6
Wen et al.
3.2
Function Representation Design
To interpret and compare heterogeneous serverless functions, this component introduces a new
semantic representation paradigm. Unlike prior work based on keywords or embeddings [11, 12,
22, 38], our design captures higher-level semantics tailored to serverless functions, encompassing
both explicit development characteristics and implicit task-level intent.
Given the diversity of programming styles, the scarcity of metadata, and the implicit semantics
embedded in code logic, direct information extraction remains challenging. To overcome them, we
leverage the code reasoning and comprehension capabilities of LLMs to extract key information
and thereby enhance the semantics of each function. Recent studies [29, 51] have demonstrated
that Prompt Engineering can effectively enhance LLM performance across various tasks. It involves
designing task-specific instructions (i.e., prompts) to guide model behavior without modifying
parameters. Through carefully crafted prompts, LLMs can thus adapt to a wide range of tasks.
Building on this, we design a structured prompt to guide the LLM in extracting critical semantic
attributes from raw function code. By coupling the prompt with a small set of curated examples
(i.e., few-shot learning [29, 47, 48]), the LLM can infer and summarize latent information according
to examples. Our prompt consists of four parts: (1) task description for the LLM query, (2) guideline
notes, (3) customized response, and (4) function code to be extracted. The overall structure is
illustrated in Fig.2, with a concrete example shown in Fig.3. We elaborate on each part below.
• The task description for the LLM query part includes both a role-play setting and a detailed
task instruction. The role-play instruction (e.g., “You are an expert writing serverless functions”) is
a widely used prompt optimization technique [51] to improve output quality. The task instruction
explicitly specifies the extraction of attribute information. As illustrated earlier in Fig. 1, serverless
functions may implement different task goals across various languages, handler interfaces tailored to
the target platform, and supported cloud services. These factors are critical to function development
and thus constitute the key extraction targets: (1) an intent summary of the serverless function, (2)
the serverless platforms used, (3) the cloud services employed, and (4) the programming languages
adopted. Moreover, the prompt embeds domain-specific examples (i.e., few-shot learning) within
the task instruction. For instance, serverless platform examples include AWS Lambda and Google
Cloud Functions; cloud service examples include AWS S3 and Google Firestore; and programming
language examples include Python and JavaScript.
• The guideline notes part is designed to help the LLM resolve ambiguities and capture implicit
associations during information extraction. They are distilled from common misclassification
patterns observed in our function analysis. First, the note clarifies that the “Serverless Framework”
is a development framework rather than a serverless platform, a distinction often confused due
to the name similarity. Second, it emphasizes that the use of certain cloud services and specific
handler interfaces generally implies the adoption of a corresponding serverless platform, even if it
is not explicitly declared in the code. These notes ensure more accurate extraction.
• The customized response part defines both the structural and content constraints for the
LLM’s output. To avoid vague or overly general responses, the LLM is instructed to return “None”
when no relevant serverless platform, cloud service, or programming language can be identified.
When such information is available, it must be organized in a standardized four-part format: Intent
Summary, Serverless Platforms, Cloud Services, and Programming Languages. This output ensures
representational consistency and simplifies subsequent information analysis.
After applying the prompt-based knowledge extraction, the structural semantic information
of each serverless function is obtained. However, identical concepts may appear under different
lexical forms across functions. For instance, the extracted programming language “JavaScript” may
be represented as “JS”. To address such inconsistencies, a mapping table is constructed to normalize
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
7
n Role: You are an expert writing serverless functions.
n Task: Please summarize [intent summary], [used serverless platforms] 
(e.g., AWS Lambda and Google Cloud Functions), [used cloud services in 
functions] (e.g., AWS S3 and Google Firestore), and [used programming 
languages] (e.g., Python and JavaScript) according to the serverless function 
below. 
Task Description for the LLM query
Customized Response
n Returns “None” if no serverless platforms, cloud services or programming 
language is identified.
n Answer Format (You MUST follow this):
Ø Intent Summary:
Ø Serverless Platforms:
Ø Cloud Services:
Ø Programming Languages:
Guideline Notes
n Serverless Framework is not a serverless platform and should not be listed 
under “Used Serverless Platforms”.
n The use of specific cloud services and handler format may implicitly suggest 
the corresponding serverless platform.
Function Code to be Extracted
n The following is function code: …
Fig. 3. The prompt of structured knowledge extraction used in SlsReuse.
terminology. Finally, we organize the extracted information as a quadruple semantic representation
{intent content, serverless platforms, cloud services, programming languages}.
A concrete semantic representation of the function in Fig. 1 is illustrated. Its intent can be
summarized via ChatGPT-4o as follows: The code defines a serverless function that responds to S3
create events. When an image file is uploaded to an S3 bucket, the function uses Amazon Rekognition to
detect labels in the image. It then tags the S3 object with the detected labels and their confidence scores.
The function includes an integration test to ensure that the image is processed correctly and tagged
with labels. To enable subsequent content similarity analysis, the intent summary is encoded into a
high-dimensional vector representation using sentence embedding models such as Sentence-BERT
(default dimensionality: 384). For example, this summary is transformed into a vector [-0.0411,
-0.0280, ..., 0.0068, -0.0334]. In addition, the extracted attributes of the function in Fig. 1 include the
serverless platform (AWS Lambda), the associated cloud services (AWS S3 and AWS Rekognition),
and the programming language (C#). These results also further suggest that LLMs can perform a
relatively effective information extraction. The final semantic-enhanced representation is therefore
expressed as {[-0.0411, -0.0280, ..., 0.0068, -0.0334], AWS Lambda, [AWS S3, AWS Rekognition], C#}.
3.3
Function Discovery and Recommendation
After the preparation phases, we enter the query phase, where relevant serverless functions are rec-
ommended based on a given task query. We employ an intent-aware discovery and recommendation
strategy. The procedure is outlined in Algorithm 1, which comprises four main steps.
Step 1: Query Understanding. Given a task query, we first derive its semantic representation
using a prompt-based structural knowledge extraction analogous to that employed in the prepa-
ration phase for serverless functions (line 2). Specifically, we obtain the key information of the
query: task intent summary 𝑇𝑄, target platforms 𝑃𝑄, desired cloud services 𝐶𝑄, and programming
languages 𝐿𝑄. 𝑉𝑄= {𝑇𝑄, 𝑃𝑄,𝐶𝑄, 𝐿𝑄} will establish a link between the high-level task query 𝑄and
the low-level function implementations F0 (lines 2-3).
Considering a task query: The generated function handler responds to S3 events on an Amazon S3
bucket and if the object is a png or jpg file uses Amazon Rekognition to detect labels. Once the labels
are found it adds them as tags to the S3 Object. This query description is extracted from the GitHub
README [2] of the function in Fig. 1. For this example, ChatGPT-4o infers the serverless platform
𝑃𝑄as AWS Lambda, the cloud services 𝐶𝑄as AWS S3 and AWS Rekognition, while the programming
language is labeled as “None” due to the absence of explicit language-specific information.
Step 2: Multi-level Pruning. To improve the efficiency of function discovery, irrelevant functions
are first pruned based on task requirements, yielding a set of relevant candidate functions for
subsequent recommendation. Our pruning process leverages extracted structural attributes for
filtering. Specifically, we analyze the query representation 𝑉𝑄and function representations F0. We
, Vol. 1, No. 1, Article . Publication date: November 2025.


8
Wen et al.
Algorithm 1: Intent-Aware Function Discovery and Recommendation
Input: Task query 𝑄in natural language
Output: Top-𝑘recommended serverless functions {𝐹1, 𝐹2, . . . , 𝐹𝑘}
1 Step 1: Query Understanding
2 Extract attribute values from 𝑄: task intent summary 𝑇𝑄, serverless platforms 𝑃𝑄, cloud
services 𝐶𝑄, programming languages 𝐿𝑄
3 Form the quadruple semantic representation of the query 𝑉𝑄= {𝑇𝑄, 𝑃𝑄,𝐶𝑄, 𝐿𝑄}
4 Initialize full function set F0 ←all semantic representations of functions in repository
5 Step 2: Multi-level Pruning
6 foreach attribute type 𝐴∈{𝑃,𝐶, 𝐿} do
7
Initialize filtered candidate set F𝐴←∅
8
Initialize exact match set F full
𝐴
←∅
9
Initialize partial match set F partial
𝐴
←∅
10
if 𝐴𝑄≠None then
// Determine whether current attribute of the query is not “None”.
11
foreach 𝐹𝑖∈F0 do
12
Extract attribute set 𝐴𝑖of 𝐹𝑖
13
Compute Jaccard Distance: 𝐽𝐴= 1 −|𝐴𝑄∩𝐴𝑖|
|𝐴𝑄∪𝐴𝑖|
14
Compute Subset Coverage: 𝑆𝐴= |𝐴𝑄∩𝐴𝑖|
|𝐴𝑄|
15
if 𝑆𝐴= 1 then
16
Add 𝐹𝑖to F full
𝐴
// Complete or Superset Match
17
else
18
Record objective vector 𝑀𝐴
𝑖= {𝐽𝐴, 1 −𝑆𝐴}
19
Add (𝐹𝑖, 𝑀𝐴
𝑖) to F partial
𝐴
20
Apply Pareto Optimization over all 𝑀𝐴
𝑖in F partial
𝐴
21
Let F pareto
𝐴
←Pareto-optimal functions
22
Merge: F𝐴←F full
𝐴
∪F pareto
𝐴
23
Update: F0 ←F𝐴
24 Step 3: Intent Similarity Calculation
25 foreach 𝐹𝑖∈F0 do
26
Encode: 𝐸𝑄= Embed(𝑇𝑄), 𝐸𝑖= Embed(𝑇𝑖) using Sentence-BERT
27
Compute cosine similarity: 𝑆𝑖= cos(𝐸𝑄, 𝐸𝑖)
28 Step 4: Top-k Recommendation
29 Sort F0 by descending 𝑆𝑖
30 Return top-𝑘serverless functions from the ranked list
first narrow the search space to functions sharing the same fundamental development attributes,
e.g., serverless platforms 𝑃, cloud services 𝐶, and languages 𝐿, as specified in the query (line 6).
For each attribute type 𝐴∈{𝑃,𝐶, 𝐿}, if the corresponding value in the task query 𝑄is not “None”,
candidate functions are matched accordingly (lines 10-23); otherwise, the procedure proceeds to the
next attribute type. This forms a multi-level pruning strategy over attribute types. Ultimately,
only functions with compatible development characteristics are retained for subsequent ranking.
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
9
We next introduce the process of generating candidate functions based on the information
associated with the current attribute type. At this process, a key challenge arises: attribute values
in a task query may contain multiple elements, such as several cloud services (e.g., Amazon S3 and
Amazon Rekognition in the example query). Functions in the repository may likewise integrate
multiple attribute values. Consequently, strict one-to-one matching is overly restrictive, while
fixed threshold-based filtering of collapsing all factors into a single weighted score risks discarding
partially relevant candidates. To address this, we formulate the relevant function discovery on
the current attribute type as a multi-objective optimization problem and, building on Pareto
optimization [35], propose a customized Pareto-based function selection method tailored to
our scenario. Rather than setting a fixed, pre-defined threshold for filtering, Pareto optimization
retains all non-dominated candidates, i.e., functions for which no other candidate performs strictly
better across all defined optimization metrics. This way preserves a diverse set of Pareto-optimal
functions. To this end, we define two complementary optimization metrics: symmetric and
asymmetric (lines 13-14). The symmetric metric, Jaccard Distance, measures the overall similarity
between the query and a candidate function based on the overlap of elements within the current
attribute type. It is computed as 𝐽𝐴= 1 −|𝐴𝑄∩𝐴𝑖|
|𝐴𝑄∪𝐴𝑖| . The value ranges from 0 to 1, where 0 indicates
complete overlap (maximum similarity) and 1 indicates no overlap (maximum dissimilarity). Owing
to its symmetry, it is well-suited for measuring holistic overlap. The asymmetric metric, Subset
Coverage, quantifies the proportion of attribute elements of the task query satisfied by the candidate
function. It is computed as 𝑆𝐴= |𝐴𝑄∩𝐴𝑖|
|𝐴𝑄| . The value also ranges from 0 to 1, where 1 indicates full
coverage of the query attributes (optimal), and 0 indicates no coverage. This is particularly important
for verifying whether a function meets core development requirements, even if it contains additional,
potentially irrelevant elements. Note that 𝐴𝑄denotes the set of elements for the given attribute
type in the task query, and 𝐴𝑖represents the corresponding set for function 𝐹𝑖. The reason for using
these two metrics is: Jaccard Distance may fail to capture the inclusion of essential elements, while
Subset Coverage may tolerate extraneous elements that introduce overhead. Integrating both within
the Pareto optimization process enables a more balanced and nuanced evaluation of candidate
functions. Based on the defined optimization metrics, potential candidate functions are selected.
First, to prioritize candidates that fully satisfy the task query, we retain all functions with complete
subset coverage (Subset Coverage = 1), including both exact and superset matches, denoted as F full
𝐴
(lines 15-16). These functions fully implement the required elements and are directly added to the
candidate set. Second, for the remaining functions with partial coverage, our Pareto-based function
selection is applied using the two defined metrics to identify non-dominated candidates, denoted
as F pareto
𝐴
, those representing optimal trade-offs between matching completeness and specificity
(lines 17-21). Finally, we merge F full
𝐴
and F pareto
𝐴
to obtain candidate set F𝐴(line 22).
This generation candidate function process is performed independently for each attribute type
(platforms 𝑃, services 𝐶, languages 𝐿). At each stage, only the retained subset F𝐴(which updates
F0) is forwarded to the next attribute filter, progressively refining the candidate functions (line 23).
Through such a multi-level pruning, the resulting set ensures both development compatibility and
requirement satisfaction. In our provided task query example, this process ultimately selects 33
candidate functions from a repository of 500 functions, as further detailed in Section 4.2.
Step 3: Intent Similarity Calculation. We further refine the candidate set F0 by evaluating
intent similarity using extracted task intent summary. Since the summary is expressed in natural
language and cannot be directly compared via string matching, we adopt Sentence-BERT to encode
intent descriptions into high-dimensional vectors (line 26). Then, we compute cosine similarity
, Vol. 1, No. 1, Article . Publication date: November 2025.


10
Wen et al.
between the task query’s intent vector and each function’s intent vector (line 27). Cosine similar-
ity [6] is a standard metric for vector comparison. In the task query example, the similarity between
its intent summary and that of the function code in Fig. 1 is 0.9001, indicating high intent relevance.
Step 4: Top-𝑘Recommendation. We recommend the top-𝑘functions with the highest intent
similarity scores, providing a ranked list of candidates that best match their task requirements. In
the task query example, the function shown in Fig. 1 is ranked first. In fact, this function is also the
correct function corresponding to the provided task query.
Complexity analysis of Algorithm 1. Let 𝑛denote the number of functions in the repository, 𝑚
the number of attribute types (a small constant, e.g., 3), 𝑑the average number of elements per
function per attribute type, and 𝑙the dimensionality of the intent vectors (e.g., 384 for Sentence-
BERT). Step 1 incurs negligible cost with constant-time query parsing. In Step 2, for each of the
constant 𝑚attribute types, the algorithm computes Jaccard Distance and Subset Coverage for 𝑛
functions in 𝑂(𝑛𝑑), followed by Pareto optimization, which requires 𝑂(𝑛2) in the worst case due
to pairwise dominance checks. Thus, this step dominates with 𝑂(𝑛2) time complexity. Step 3
performs similarity calculation for each function (in the worst-case scenario where all 𝑛functions
are retained as candidates) and the query, resulting in a cost of 𝑂(𝑛𝑙). Step 4 sorts the results in
𝑂(𝑛𝑙𝑜𝑔𝑛). Overall, the total time complexity is 𝑂(𝑛2 + 𝑛𝑙+ 𝑛𝑙𝑜𝑔𝑛), which simplifies to 𝑂(𝑛2) as the
dominant term. For the space complexity, the algorithm stores function attributes (𝑂(𝑛𝑑)), intent
vectors (𝑂(𝑛𝑙)), and Pareto vectors (𝑂(𝑚𝑛)), leading to total space complexity 𝑂(𝑛(𝑑+ 𝑙+ 𝑚)),
which reduces 𝑂(𝑛𝑙) assuming 𝑑and 𝑚are constants. Overall, Algorithm 1 is quadratic in time
and linear in space with respect to the number of functions.
3.4
Implementation
We implement SlsReuse as a Python-based prototype. The design is language- and platform-agnostic,
making it applicable to serverless function analysis across diverse programming languages and
serverless platforms, as well as to function recommendation for arbitrary task queries. The imple-
mentation is fully encapsulated within the tool and remains transparent to developers. In practice,
developers only need to provide requirement descriptions through the tool interface, without addi-
tional effort. For each task query, SlsReuse generated a ranked list of relevant serverless functions,
each linked directly to its original implementation. The core analysis is built upon and enhanced
by advanced libraries, including OpenAI API, Scikit-learn, and Sentence Transformers.
4
EXPERIMENTAL EVALUATION
4.1
Research Questions
• RQ1: How does the semantic-enhanced representation of SlsReuse perform compared with
traditional methods?
• RQ2: What is the advantage of SlsReuse in leveraging multi-level pruning for recommendation?
• RQ3: How does the non-determinism of LLMs influence the effectiveness of SlsReuse?
• RQ4: How well does SlsReuse generalize when applied with different LLMs?
4.2
Reusable Serverless Function Dataset
Given the lack of reusable functions in current serverless ecosystems, we construct a dedicated
dataset following the construction principles outlined in Section 3.1. We first survey widely adopted
open-source benchmarks from both academia [27, 33, 50] and industry [4], including Function-
Bench[27], ServerlessBench[50], AWS Samples[3], SeBS[14], and FaaSDom [33]. Based on these
sources, we apply our filtering process to curate a final set of 500 high-quality serverless functions
spanning diverse domains, including Web request handling, video processing, scientific computing,
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
11
machine learning, and natural language processing. This dataset size is sufficient as it is comparable
to, or even larger than, datasets employed in prior code search [31, 32]. Moreover, our dataset
encompasses functions from major serverless platforms (AWS Lambda, Google Cloud Functions,
Microsoft Azure Functions, and Apache OpenWhisk) and supports a broad set of programming
languages, including Python, Ruby, JavaScript, Java, C++, C#, and Go. This language diversity not
only mirrors the heterogeneity of real-world serverless ecosystems but also surpasses the scope of
language support reported in prior works [12, 31, 36, 37, 41].
4.3
Compared Baselines
In the absence of established approaches for serverless function reuse, we evaluate SlsReuse against
two representative traditional methods adapted for function recommendation. We also introduce a
customized LLM-based variant as a baseline to explore the additional advantages of SlsReuse.
• Keyword-based method: SNIFF [12] is a classical code search approach that supports free-form
natural language queries about programming tasks. It processes the query and code by applying
stop-word removal and stemming, treating them as a bag-of-words. Following this core idea, we
adapt it to the serverless function recommendation: both the task query and the function code are
preprocessed identically (stop-word removal and stemming), and candidate functions are retrieved
if they contain all query keywords. As exact matches across all query keywords are uncommon, we
relax this constraint and rank candidate functions in descending order of keyword match counts.
• Embedding-based method: UNIF [11] is a leading text-to-code embedding method, which directly
maps queries and code into dense embedding vectors. Code fragments semantically related to a
query are discovered by computing similarity between their vectors. In our adaptation, the task
query is encoded into a dense embedding vector using a pre-trained sentence encoder, and each
serverless function is represented by a precomputed embedding vector derived from its textual
information (e.g., function name, docstring, and source code). Candidate functions are ranked by
computing the cosine similarity between the query embedding and the function embeddings.
• Customized LLM-based variant method: This baseline employs a prompt-based strategy in
which LLMs directly generate intent summaries without extracting other information (e.g., plat-
form, programming language, cloud service). The prompt consists of either the raw serverless
function code or the task query, combined with an instruction to produce an intent summary. The
resulting summaries are encoded into semantic vectors using a pre-trained sentence encoder, and
recommendations are derived by computing cosine similarity. In contrast to SlsReuse, this method
does not incorporate multi-level structural information extraction and candidate pruning.
4.4
Experimental Settings
Parameter Settings. For RQ1, we compare SlsReuse with key-based method and embedding-based
method. No parameter tuning is required. For RQ2, we compare SlsReuse with the customized
LLM-based variant method, as both employ LLMs as a core component. We adopt ChatGPT-
4o as the default LLM, owing to its wide adoption and demonstrated effectiveness in recent
studies [29, 51]. A critical hyperparameter in LLM-based generation is the temperature, which
controls the randomness of the output. To ensure reproducibility and deterministic behavior, we
follow prior work [13, 23, 47, 48] and fix the temperature to 0 for all identical queries. In this RQ,
we further evaluate SlsReuse against both key-based and embedding-based approaches, with a focus
on recommendation latency. For RQ3, we maintain the default temperature at 0 to analyze the
non-determinism of LLMs under controlled conditions, and further vary it to 0.2 and 0.5 to examine
the robustness of SlsReuse in other temperature settings. For RQ4, we investigate the generalization
capability of SlsReuse across diverse leading LLMs beyond ChatGPT-4o. Specifically, we evaluate
the top-ranked open-source model Llama 3.1 (405B) Instruct Turbo, the proprietary Gemini 2.0
, Vol. 1, No. 1, Article . Publication date: November 2025.


12
Wen et al.
Flash, and the widely adopted DeepSeek V3. Following the RQ2 setting, the temperature is fixed to
0 for all LLMs to ensure deterministic outputs.
Evaluation Strategy and Metrics. We evaluate SlsReuse against baselines by generating a ranked
list of candidate functions for each task query. Due to the absence of publicly available query
datasets for serverless function recommendations, we construct a synthetic query dataset to enable
evaluation. This dataset requires that each task query be validated with the corresponding correct
function, i.e., the ground-truth function. To this end, we extract 150 task descriptions from the
README files of the collected functions. When the README file of a function provides a specific
and well-defined task description, we treat this description as a task query from the developer and
designate the corresponding function as the ground truth. The size of our dataset surpasses that of
previous query datasets [11, 12, 24, 36, 37, 41]. We then use the following evaluation metrics.
• Recall@𝑘. For each method, we compute Recall@𝑘by checking whether the ground-truth
function appears within the top-𝑘recommended results. The value of 𝑘is adjusted to different
settings, including 1, 5, 10, 15, and 20. This metric measures the coverage of recommendations
for a given method, i.e., the proportion of task queries for which the ground-truth function is
recommended within the top-𝑘positions. Recall@𝑘ranges from 0 to 100%, with higher values
indicating stronger coverage and more effective function discovery.
• MRR@𝑘. Mean Reciprocal Rank (MRR) measures how early the ground-truth function appears
in the ranked list. For each task query, the reciprocal rank is defined as the inverse of the rank
position of the ground-truth function. If the ground-truth function does not occur within the top-𝑘
results, the reciprocal rank is set to zero. MRR@𝑘is then computed as the average reciprocal rank
across all queries. MRR@𝑘= 1
𝑁
Í𝑁
𝑖=1
1
rank𝑖, where 𝑁is the number of task queries and rank𝑖denotes
the position of ground-truth function for query 𝑖in the top-𝑘list. The value of MRR@𝑘ranges from
0 to 1, with higher values indicating that correct functions tend to be ranked earlier.
• RecLatency. We define the recommendation latency as the time elapsed from the submission of
a task query to the completion of generating the recommendation list. RecLatency is reported as
the average latency across all task queries, reflecting the efficiency of function discovery.
Experimental Repetitions. To account for stochastic variability in experiments involving ran-
domness, we follow established best practices [23, 45, 47] by repeating each experiment five times.
Reported results correspond to the mean values of the evaluation metrics across these runs, thereby
reducing the effect of random fluctuations and enhancing result reliability.
Experimental Environment. All experiments were conducted on an Ubuntu 18.04.4 LTS server
equipped with an Intel Xeon (R) 4-core processor and 24 GiB of memory. Access to LLMs was
obtained by their respective APIs.
5
EVALUATION RESULTS
5.1
Results of RQ1: Effectiveness of SlsReuse and Traditional Baselines
We explore the effectiveness of the semantic-enhanced representation introduced by SlsReuse
against two traditional baselines. As shown in Table 1, SlsReuse demonstrates significant advantages
in Recall@k and MRR@k. We will introduce the results of each evaluation metric. For Recall@k,
results show that SlsReuse consistently discovers the ground-truth function with higher coverage,
highlighting its superior effectiveness. Specifically, SlsReuse achieves Recall@1 of 52.13%, Recall@5
of 86.13%, Recall@10 of 91.20%, Recall@15 of 92.67%, and Recall@20 of 92.93%. In contrast, the
keyword-based method yields lower values of 16.67%, 32.00%, 42.00%, 48.67%, and 52.00% at the same
cutoffs. The embedding-based method outperforms the keyword-based method but lags behind
SlsReuse, with corresponding values of 23.33%, 50.67%, 66.67%, 74.00%, and 77.33%. Relative to the
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
13
Table 1. (RQ1) Recall@𝑘and MRR@𝑘results for two traditional baseline methods and SlsReuse.
Metrics
Methods
𝑘= 1
𝑘= 5
𝑘= 10
𝑘= 15
𝑘= 20
Recall@𝑘
(Improved
percentage
points)
Keyword-based method
16.67%
32.00%
42.00%
48.67%
52.00%
Embedding-based method
23.33%
50.67%
66.67%
74.00%
77.33%
SlsReuse
(vs. Keyword)
52.13%
(↑35.47)
86.13%
(↑54.13)
91.20%
(↑49.20)
92.67%
(↑44.00)
92.93%
(↑40.93)
(vs. Embedding)
(↑28.80)
(↑35.47)
(↑24.53)
(↑18.67)
(↑15.60)
MRR@𝑘
(Improved
percentage)
Keyword-based method
0.1667
0.2153
0.2291
0.2345
0.2363
Embedding-based method
0.2333
0.3389
0.3593
0.3650
0.3669
SlsReuse
(vs. Keyword)
0.5240
(↑214.40%)
0.6547
(↑204.05%)
0.6616
(↑188.77%)
0.6628
(↑182.66%)
0.6629
(↑180.50%)
(vs. Embedding)
(↑124.57%)
(↑93.19%)
(↑84.15%)
(↑81.58%)
(↑80.70%)
keyword-based method, SlsReuse improves recall by 35.47, 54.13, 49.20, 44.00, and 40.93 percentage
points across the five cutoffs. Compared to the embedding-based method, the improvements of
SlsReuse are 28.80, 35.47, 24.53, 18.67, and 15.60 percentage points, respectively. In particular,
Recall@1 of SlsReuse (52.13%) not only far exceeds that of the keyword-based method at Recall@1
(16.67%), but also surpasses the result of the keyword-based method even at Recall@20 (52.00%).
This indicates that SlsReuse delivers higher discovery effectiveness.
For MRR@k, SlsReuse demonstrates high ranking quality, as the ground-truth functions are more
likely to appear earlier in the results. Specifically, SlsReuse achieves MRR@1 = 0.5240, MRR@5 =
0.6547, MRR@10 = 0.6616, MRR@15 = 0.6628, and MRR@20 = 0.6629. In contrast, the keyword-based
method yields 0.1667, 0.2153, 0.2291, 0.2345, and 0.2363, while the embedding-based method attains
0.2333, 0.3389, 0.3593, 0.3650, and 0.3669, respectively. Relative to the keyword-based method,
SlsReuse improves 214.40%, 204.05%, 188.77%, 182.66% and 180.50%, and compared to the embedding-
based method, by 124.57%, 93.19%, 84.15%, 81.58% and 80.70%. All three approaches exhibit a
noticeable increase from MRR@1 to MRR@5, after which the values grow marginally and gradually
converge. SlsReuse shows an improvement (0.5240 to 0.6547) compared with the keyword-based
(0.1667 to 0.2153) and embedding-based (0.2333 to 0.3389) methods. Beyond MRR@5, performance
stabilizes, with the keyword-based method plateauing near 0.23, the embedding-based method near
0.36, and SlsReuse maintaining a substantially higher level around 0.66.
We further analyze the reasons behind the poor effectiveness of the two baselines. For the
keyword-based method, two limitations are identified. First, the keyword match rate is inherently
low. Among the 150 evaluated task queries, the average number of matched keywords for the
ground-truth functions is only 7.92. This gap arises because queries generally employ everyday
vocabulary and synonyms, whereas function implementations predominantly rely on technical jar-
gon, library-specific naming conversions, and abbreviations. Such a lexical mismatch substantially
reduces keyword coverage, even after applying standard preprocessing techniques such as stop-
word removal and stemming. Second, this method fails to capture the discriminative features that
characterize functional intent. We analyze keyword frequency and reveal that high-frequency key-
words such as “exampl” (106 occurrences), “use” (88 occurrences), and “demonstr” (65 occurrences)
dominate the matching process. These keywords are generic and semantically uninformative,
contributing little to distinguishing the task goal from the code functionality. As a result, the
keyword-based method struggles to identify the ground truth functions, leading to low recall and
MRR scores. Overall, the keyword-based method lacks the capacity to model semantic relevance at
a higher level, making it relatively ineffective.
For the embedding-based method, several limitations are observed. First, embeddings learned by
this method primarily rely on surface vocabularies. Due to the inherent inconsistency between task
, Vol. 1, No. 1, Article . Publication date: November 2025.


14
Wen et al.
queries and function implementations, it introduces semantic bias and results in weak similarity
and suboptimal recommendations. Second, embeddings generated from general-purpose language
models are not optimized for code-specific semantics. They fail to capture functional characteristics
of program logic, such as serverless platform usage patterns, languages, or task goals. As a result,
the semantic gap between how functionality is expressed in natural language task queries and
how it is encoded in function implementations remains unbridged. Finally, embeddings tend to
dilute task-specific signals by overemphasizing frequent but non-discriminative terms, leading to
insufficient differentiation between functions with similar lexical content but distinct functional
purposes. Overall, while the embedding-based method can partially capture task query intent, it
struggles to represent code functionality intent due to the abstract and heterogeneous nature of
code expression. Thus, this baseline cannot establish strong alignment with task queries.
By contrast, SlsReuse addresses these limitations by introducing a semantic-enhanced represen-
tation that models richer relationships between task queries and function implementations at a
deeper semantic level. It explicitly mines the underlying functionality intent from code structures.
Ans. to RQ1: For recommendation quality, SlsReuse achieves Recall@1 of 52.13%, Recall@5 of
86.13%, Recall@10 of 91.20%, Recall@15 of 92.67%, and Recall@20 of 92.93%, surpassing the state-
of-the-art embedding-based baseline by 28.80, 35.47, 24.53, 18.67, and 15.60 percentage points,
respectively. For ranking quality, SlsReuse attains MRR@1 of 0.5240, MRR@5 of 0.6547, MRR@10
of 0.6616, MRR@15 of 0.6628, and MRR@20 of 0.6629, corresponding to relative improvements
of 124.57%, 93.19%, 84.15%, 81.58%, and 80.70% over the same baseline. These results suggest the
effectiveness of the core semantic-enhanced representation design of SlsReuse.
5.2
Results of RQ2: Advantage of Multi-Level Structural Pruning
0.00
0.25
0.50
0.75
1.00
0%
25%
50%
75%
100%
k=1
k=5
k=10
k=15
k=20
Mrr 
Recall (%)
Recall-SlsRecommender
MRR-SlsRecommender
MRR-LLM-based variant method
Recall-LLM-based variant method
Fig. 4. (RQ2) Recall@k and MRR@k results of
SlsReuse and the customized LLM-based variant.
310.68 ms
92.50 ms
85.32 ms
47.47 ms
0
50
100
150
200
250
300
350
400
Keyword-based
method
Embedding-based
method
LLM-based
variant method
SlsRecommender
RecLatency (milliseconds)
difference: 263.21
(vs. ours ↑554.50%)
difference: 45.03
(vs. ours ↑94.87%)
difference: 37.85
(vs. ours ↑79.73%)
Short Latency is Better!
Fig. 5. (RQ2) Recommendation latency comparisons
between SlsReuse and three baselines.
To assess the additional benefits of SlsReuse, we compare it with a customized LLM-based variant
that omits the multi-level structural pruning step. As shown in Fig. 4, SlsReuse achieves recall and
MRR scores comparable to those of the variant across different 𝑘values. This indicates that both
methods are similarly effective in retrieving relevant functions. The performance of the customized
variant is expected, as it still adheres to the same principle of aligning task queries with function-
level intent, thereby enabling the identification of semantically related candidates. The comparable
results of SlsReuse confirm that multi-level pruning retains the vast majority of relevant candidates,
validating its effectiveness without compromising accuracy.
We further evaluate the recommendation latency of SlsReuse against three baselines. As shown
in Fig. 5, SlsReuse achieves an average latency of 47.47 ms, significantly faster than the customized
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
15
LLM-based variant (85.32 ms), the keyword-based method (310.68 ms), and the embedding-based
method (92.50 ms). In absolute terms, the customized LLM-based variant is slower by 37.85 ms
(79.73% longer than SlsReuse), the keyword-based method by 263.21 ms (554.50% longer), and the
embedding-based method by 45.03 ms (94.87% longer). From the perspective of SlsReuse, it reduces
the recommendation latency by 44.36%, 84.72%, and 48.68% compared with the three baselines,
demonstrating clear efficiency advantages. The major bottleneck for baselines is that they compute
similarity scores exhaustively against all candidate functions, incurring considerable overhead.
By contrast, SlsReuse leverages a multi-level pruning strategy grounded in structural information
(e.g., serverless platforms, programming languages, and cloud services), which narrows the search
space. We further analyze the candidate set size after applying our multi-level pruning for each
task query. On average, fewer than 40% of functions remain for subsequent similarity computation,
thereby substantially reducing the search space and improving recommendation efficiency. These
results show that SlsReuse not only achieves effective recommendation results but also delivers
significantly lower recommendation latency, underscoring its practical applicability.
Ans. to RQ2: SlsReuse preserves most relevant candidates even with multi-level pruning,
demonstrating the effectiveness of its pruning strategy. Moreover, it achieves an average
recommendation latency of 47.47 ms, representing reductions of 44.36%, 84.72%, and 48.68%
compared with the LLM-based variant, the keyword-based method, and the embedding-based
method, respectively. These results highlight the recommendation efficiency of SlsReuse.
5.3
Results of RQ3: Impact of Non-determinism on SlsReuse
We investigate the impact of LLM non-determinism on evaluation results under a default tem-
perature setting of 0. As described in Section 4.4, each experiment is repeated five times, and we
report Recall@k and MRR@k at different cutoff values (Table 2). Results show that while LLM
non-determinism introduces fluctuations, its effect is relatively limited, with recall varying within
approximately 5 percentage points and MRR differing by no more than 0.06 across trials in different
𝑘. Under temperature 0, SlsReuse consistently shows strong effectiveness. Specifically, Recall@1
ranges from 49.33% to 56.67%, Recall@5 from 83.33% to 88.00%, Recall@10 from 86.67% to 93.33%,
Recall@15 from 89.33% to 94.00%, and Recall@20 from 89.33% to 94.67%. Particularly, even the
lowest values at each cutoff (e.g., 83.33% at Recall@5 and 86.67% at Recall@10) still surpass both
keyword-based and embedding-based baselines. A similar trend is observed for MRR@k, further
confirming that the observed superiority of SlsReuse is robust to the non-determinism of LLMs.
To further assess the robustness of SlsReuse, we analyze the experimental results at temperatures
0.2 and 0.5. As shown in Table 2, there is a relatively minor impact. When the temperature is 0.2,
the recall variance is about 3% and the MRR variance is about 0.03 across all repetitions in all 𝑘
values. When the temperature is 0.5, the recall variance is about 5% and the MRR variance is about
0.06 across all repetitions. From the results, the temperature of 0.5 has more randomness than
that of 0.2. It is reasonable that the higher the temperature setting, the greater the randomness.
Specifically, when the temperature is set to 0.2, Recall@1 ranges from 49.33% to 54.67%, Recall@5
from 82.00% to 85.33%, Recall@10 from 90.67% to 92.00%, Recall@15 from 91.33% to 94.00%, and
Recall@20 from 91.33% to 95.33%, with respective differences of 5.33, 3.33, 1.33, 2.67, and 4.00
percentage points. The corresponding MRR values are 0.4933–0.5467 for MRR@1, 0.6257–0.6583 for
MRR@5, 0.6373–0.6686 for MRR@10, 0.6384–0.6691 for MRR@15, and 0.6388–0.6705 for MRR@20,
with variations of 0.0533, 0.0327, 0.0313, 0.0307, and 0.0317, respectively. At temperature = 0.5, the
fluctuations are slightly larger. Recall@1 ranges from 44.67% to 49.33%, Recall@5 from 79.33% to
86.67%, Recall@10 from 86.00% to 90.67%, Recall@15 from 88.00% to 91.33%, and Recall@20 from
, Vol. 1, No. 1, Article . Publication date: November 2025.


16
Wen et al.
Table 2. (RQ3) Recall@k and MRR@k results of SlsReuse across five repetitions.
𝑘values
Temperature
Repetition 1
Repetition 2
Repetition 3
Repetition 4
Repetition 5
Mean
temperature=0
49.33% /
0.4933
52.67% /
0.5400
56.67% /
0.5667
50.67% /
0.5067
51.33% /
0.5133
52.13% /
0.5240
𝑘= 1
temperature=0.2
54.00% /
0.5400
51.33% /
0.5133
50.00% /
0.5000
49.33% /
0.4933
54.67% /
0.5467
51.87% /
0.5187
(recall /
MRR)
temperature=0.5
48.00% /
0.4800
44.67% /
0.4467
49.33% /
0.4933
47.33% /
0.4733
46.67% /
0.4667
47.20% /
0.4720
temperature=0
83.33% /
0.6219
87.33% /
0.6633
88.00% /
0.6893
86.67% /
0.6496
85.33% /
0.6494
86.13% /
0.6547
𝑘= 5
temperature=0.2
84.00% /
0.6471
82.00% /
0.6287
83.33% /
0.6257
85.33% /
0.6297
84.67% /
0.6583
83.87% /
0.6379
(recall /
MRR)
temperature=0.5
79.33% /
0.5958
82.00% /
0.5926
81.33% /
0.6210
80.00% /
0.5953
86.67% /
0.6064
81.87% /
0.6022
temperature=0
86.67% /
0.6273
90.67% /
0.6676
92.67% /
0.6958
93.33% /
0.6581
92.67% /
0.6593
91.20% /
0.6616
𝑘= 10
temperature=0.2
92.00% /
0.6581
90.67% /
0.6407
92.00% /
0.6373
90.67% /
0.6375
92.00% /
0.6687
91.47% /
0.6485
(recall /
MRR)
temperature=0.5
88.67% /
0.6079
90.00% /
0.6034
88.67% /
0.6316
86.00% /
0.6042
90.67% /
0.6124
88.80% /
0.6119
temperature=0
89.33% /
0.6293
92.67% /
0.6689
94.00% /
0.6969
94.00% /
0.6587
93.33% /
0.6598
92.67% /
0.6628
𝑘= 15
temperature=0.2
94.00% /
0.6598
91.33% /
0.6412
93.33% /
0.6384
92.67% /
0.6389
92.67% /
0.6691
92.80% /
0.6495
(recall /
MRR)
temperature=0.5
90.67% /
0.6096
90.67% /
0.6040
90.67% /
0.6333
88.00% /
0.6060
91.33% /
0.6129
90.27% /
0.6132
temperature=0
89.33% /
0.6293
92.67% /
0.6690
94.67% /
0.6972
94.00% /
0.6587
94.00% /
0.6602
92.93% /
0.6629
𝑘= 20
temperature=0.2
94.00% /
0.6598
91.33% /
0.6412
94.00% /
0.6388
93.33% /
0.6394
95.33% /
0.6705
93.60% /
0.6499
(recall /
MRR)
temperature=0.5
91.33% /
0.6100
90.67% /
0.6040
91.33% /
0.6337
88.67% /
0.6063
93.33% /
0.6140
91.07% /
0.6136
88.67% to 93.33%, with respective differences of 4.67, 7.33, 4.67, 3.33, and 4.67 percentage points. For
MRR, MRR@1 ranges from 0.4467 to 0.4933, MRR@5 from 0.5926 to 0.6210, MRR@10 from 0.6034
to 0.6316, MRR@15 from 0.6040 to 0.6333, and MRR@20 from 0.6040 to 0.6337, with respective
differences of 0.0733, 0.0674, 0.0685, 0.0676, and 0.0680. Despite these variations, the effectiveness
of SlsReuse remains consistently high across all evaluation metrics and is comparable to the default
setting (temperature = 0). Particularly, even the lowest observed values across all metrics still
outperform the keyword-based and embedding-based baselines. These experimental results confirm
the strong robustness of SlsReuse.
Ans. to RQ3: The non-determinism of LLMs does not affect the validity of our conclusions.
5.4
Results of RQ4: Generalization Capability of SlsReuse
To explore the generalization capability of SlsReuse, we further experiment with three additional
LLMs: Llama 3.1 (405B) Instruct Turbo, Gemini 2.0 Flash, and DeepSeek V3. As shown in Fig. 3,
SlsReuse consistently delivers high effectiveness across all models, achieving Recall@20 above 80%
and 𝑀𝑅𝑅@20 above 0.55. Specifically, with the Llama 3.1 (405B) Instruct Turbo, SlsReuse achieves
Recall@1 = 48.67%, Recall@5 = 81.87%, Recall@10 = 86.40%, Recall@15 = 87.87%, and Recall@20
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
17
Table 3. (RQ4) Recall@k and MRR@k results about SlsReuse using various LLMs.
LLMs
k = 1
k = 5
k = 10
k = 15
k = 20
ChatGPT-4o
52.13% / 0.5240
86.13% / 0.6547
91.20% / 0.6616
92.67% / 0.6628
92.93% / 0.6629
Llama 3.1 (405B)
Instruct Turbo
48.67% / 0.4867
81.87% / 0.6109
86.40% / 0.6171
87.87% / 0.6182
88.40% / 0.6185
Gemini 2.0 Flash
42.40% / 0.4240
76.80% / 0.5525
81.73% / 0.5594
82.13% / 0.5597
83.60% / 0.5605
DeepSeek V3
44.27% / 0.4427
74.67% / 0.5631
81.20% / 0.5717
83.47% / 0.5735
84.40% / 0.5740
= 88.40%, with corresponding MRR@1 = 0.4867, MRR@5 = 0.6109, MRR@10 = 0.6171, MRR@15 =
0.6182, and MRR@20 = 0.6185. For the Gemini 2.0 Flash, the results are Recall@1 = 42.40%, Recall@5
= 76.80%, Recall@10 = 81.73%, Recall@15 = 82.13%, and Recall@20 = 83.60%, with MRR@1 = 0.4240,
MRR@5 = 0.5525, MRR@10 = 0.5594, MRR@15 = 0.5597, and MRR@20 = 0.5605. With the DeepSeek
V3, SlsReuse achieves Recall@1 = 44.27%, Recall@5 = 74.67%, Recall@10 = 81.20%, Recall@15 = 83.47%,
and Recall@20 = 84.40%, with MRR@1 = 0.4427, MRR@5 = 0.5631, MRR@10 = 0.5717, MRR@15 =
0.5735, and MRR@20 = 0.5740. Overall, the better effectiveness is observed with ChatGPT-4o and
Llama 3.1 (405B) Instruct Turbo, while Gemini 2.0 flash model and DeepSeek V3 achieve slightly
lower metrics but still maintain high Recall values (83.60% and 84.40% at 𝑘= 20).
We further investigate the reasons why Gemini 2.0 Flash and DeepSeek V3 exhibit comparatively
weaker performance. Our analysis indicates that both models exhibit weaknesses in structural
knowledge extraction, particularly in recognizing serverless platforms. On average, 7–9 task queries
per evaluation round yield incorrect results due to platform misclassification, which directly lowers
recall and MRR. This suggests that the inferior performance of Gemini 2.0 Flash and DeepSeek V3
arises from inherent limitations in structured metadata inference.
Ans. to RQ4: SlsReuse exhibits generalization capability, consistently yielding effective results
across diverse LLMs. SlsReuse achieves better effectiveness when combined with ChatGPT-4o
and Llama 3.1 (405B) Instruct Turbo.
6
THREATS TO VALIDITY
Evaluation Query Data. Since no publicly available query datasets exist for serverless function
recommendation, we construct a dedicated dataset for evaluation. A potential threat to validity arises
from the absence of real developer-requirement queries. To mitigate this issue, we systematically
analyze a curated repository of reusable serverless functions and identify cases where original
function descriptions can be reasonably reinterpreted as developer queries. In these cases, the
corresponding functions are treated as ground-truth recommendations. This strategy ensures that
the constructed dataset remains both verifiable and representative of practical usage scenarios.
Data Leakage Concerns. A potential threat is data leakage, since LLMs are pretrained on large-
scale corpora that may include open-source code and serverless platform examples. As a result,
models may have been exposed to content resembling the functions or queries used in our evaluation.
We regard the impact on our results as negligible for two reasons. First, our function repository
and evaluation queries are manually curated and refined into task-oriented requirements, reducing
the likelihood of direct overlap with pretraining data. Second, our study focuses on structured
information extraction, which requires contextual reasoning rather than rote memorization. Thus,
even if partial overlap exists, it is unlikely to compromise the validity of our conclusions.
, Vol. 1, No. 1, Article . Publication date: November 2025.


18
Wen et al.
7
RELATED WORK
Serverless Computing. The rapid adoption of serverless computing has spurred substantial
research interest, leading to broad studies, such as performance characterization and testing [27,
33, 45, 50], performance optimization [15, 30], usage characterization [16, 25, 39], and development
challenges [44]. For example, FunctionBench [27] provided a benchmark suite for evaluating
serverless function performance across multiple platforms. SCOPE [45] introduced a performance
testing method to address performance variance problems in function executions. To improve
resource provisioning, Sizeless [15] was presented as a predictive approach that selects optimal
resource configurations. From a usage perspective, Eismann et al.[16] conducted an empirical
analysis of serverless functions, providing insights into their structural and operational properties.
Wen et al.[44] identified 36 challenges in function development, underscoring key obstacles to
developer productivity. Despite these advances, the challenge of enabling effective serverless
function reuse remains unresolved. This paper fills this gap by proposing SlsReuse.
Code Recommendation Studies. This paper centers on function code recommendations. Prior
research closely related to our study can be grouped into two directions: natural language–to–code
recommendation and code-to-code recommendation. First, natural language–to–code recommen-
dation has investigated methods for discovering or generating code snippets from natural language
queries [11, 12, 20, 22, 38]. For instance, Que2Code [20] identified relevant code snippets for queries
by leveraging Stack Overflow posts. However, it is limited to fragmentary code solutions and cannot
deliver complete function implementations. SNIFF [12] supported keyword-based matching to
enhance code discovery from queries. We compare this method with SlsReuse in Section 5.1. SlsReuse
achieves substantial recall improvements of 35.47–54.13 percentage points. Recent approaches have
investigated mapping between queries and source code [11, 22, 38]. For example, NCS [22] and
UNIF [11] leveraged neural networks to jointly embed source code and natural language queries
into a shared space. We also compare SlsReuse with UNIF, one of the most effective text-to-code
recommendation methods [11]. SlsReuse improves recall by 15.60–35.47 percentage points over
UNIF. The reasons for the limited effectiveness of these methods are discussed in Section 5.1.
A separate line of research has explored code recommendation from code queries [28, 31, 34, 41].
AROMA [31] indexed Java methods, clustered candidates, and intersected retrieval results to
produce concise code snippets that captured usage patterns. GROUM [34] modeled code as graphs
to represent method calls and control-flow dependencies, enabling fine-grained pattern matching for
Android applications. While effective, these approaches target code fragment similarity, whereas our
work addresses recommending reusable serverless functions from natural language requirements.
8
CONCLUSION
In this paper, we presented SlsReuse, the first LLM-powered framework for serverless function
reuse. By constructing a reusable function repository and employing prompt-engineered semantic
enhancement, SlsReuse bridged the gap between natural language queries and heterogeneous
function implementations. Its intent-aware function discovery, enhanced by multi-level pruning
and similarity ranking, enabled matching of task queries to reusable functions. Evaluation on 110
task queries showed that SlsReuse significantly outperformed the state-of-the-art method, achiev-
ing Recall@1 and Recall@10 gains of 28.80 and 24.53 percentage points, respectively. Additional
experiments with ChatGPT-4o, Llama 3.1 (405B) Instruct Turbo, Gemini 2.0 Flash, and DeepSeek V3
demonstrate the generalization of SlsReuse, confirming its consistent effectiveness across models.
REFERENCES
[1] 2025. AWS Lambda. https://docs.aws.amazon.com/lambda.
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
19
[2] 2025.
AWS Lambda S3 and Image Rekognition Function Project.
https://github.com/aws/aws-lambda-
dotnet/tree/jangirg/chore/release-annotations-0.4.3.0/Blueprints/BlueprintDefinitions/vs2017/DetectImageLabels/
template/src/BlueprintBaseName.1.
[3] 2025. AWS samples. https://github.com/aws-samples.
[4] 2025. AWS serverless repository. https://serverlessrepo.aws.amazon.com/applications.
[5] 2025. Azure Functions. https://docs.microsoft.com/en-us/azure/azure-functions/.
[6] 2025. Cosine similarity. https://en.wikipedia.org/wiki/Cosine_similarity.
[7] 2025. Google Cloud Functions. https://cloud.google.com/functions.
[8] 2025. Learning serverless (and why it is hard). https://pauldjohnston.medium.com/learning-serverless-and-why-it-is-
hard-4a53b390c63d.
[9] 2025. A research and markets report. https://omdia.tech.informa.com/pr/2024/jun/omdia-serverless-computing-
valued-at-19-billion-dollars-is-the-fastest-growing-cloud-service.
[10] Lixiang Ao, Liz Izhikevich, Geoffrey M Voelker, and George Porter. 2018. Sprocket: A serverless video processing
framework. In Proceedings of the ACM Symposium on Cloud Computing. 263–274.
[11] Jose Cambronero, Hongyu Li, Seohyun Kim, Koushik Sen, and Satish Chandra. 2019. When deep learning met code
search. In Proceedings of the ACM Joint Meeting on European Software Engineering Conference and Symposium on the
Foundations of Software Engineering. 964–974.
[12] Shaunak Chatterjee, Sudeep Juvekar, and Koushik Sen. 2009. Sniff: A search engine for Java using free-form queries.
In Proceedings of the Fundamental Approaches to Software Engineering. Springer, 385–400.
[13] Yinfang Chen, Huaibing Xie, Minghua Ma, Yu Kang, Xin Gao, Liu Shi, Yunjie Cao, Xuedong Gao, Hao Fan, Ming Wen,
et al. 2024. Automatic root cause analysis via large language models for cloud incidents. In Proceedings of the European
Conference on Computer Systems. 674–688.
[14] Marcin Copik, Grzegorz Kwasniewski, Maciej Besta, Michal Podstawski, and Torsten Hoefler. 2021. SeBS: A serverless
benchmark suite for Function-as-a-Service computing. In Proceedings of the International Middleware Conference.
64–78.
[15] Simon Eismann, Long Bui, Johannes Grohmann, Cristina Abad, Nikolas Herbst, and Samuel Kounev. 2021. Sizeless:
Predicting the optimal size of serverless functions. In Proceedings of the International Middleware Conference. 248–259.
[16] Simon Eismann, Joel Scheuner, Erwin Van Eyk, Maximilian Schwinger, Johannes Grohmann, Nikolas Herbst, Cristina
Abad, and Alexandru Iosup. 2021. The state of serverless applications: collection, characterization, and community
consensus. IEEE Transactions on Software Engineering (2021).
[17] Jonatan Enes, Roberto R Expósito, and Juan Touriño. 2020. Real-time resource scaling platform for big data workloads
on serverless environments. Future Generation Computer Systems 105 (2020), 361–379.
[18] Zhiyu Fan, Xiang Gao, Martin Mirchev, Abhik Roychoudhury, and Shin Hwei Tan. 2023. Automated repair of programs
from large language models. In Proceedings of the IEEE/ACM International Conference on Software Engineering. IEEE,
1469–1481.
[19] Sadjad Fouladi, Riad S Wahby, Brennan Shacklett, Karthikeyan Vasuki Balasubramaniam, William Zeng, Rahul
Bhalerao, Anirudh Sivaraman, George Porter, and Keith Winstein. 2017. Encoding, fast and slow: Low-Latency video
processing using thousands of tiny threads. In Proceedings of the USENIX Symposium on Networked Systems Design and
Implementation. 363–376.
[20] Zhipeng Gao, Xin Xia, David Lo, John Grundy, Xindong Zhang, and Zhenchang Xing. 2023. I know what you are
searching for: Code snippet recommendation from Stack Overflow posts. ACM Transactions on Software Engineering
and Methodology 32, 3 (2023), 1–42.
[21] Vicent Giménez-Alventosa, Germán Moltó, and Miguel Caballer. 2019. A framework and a performance assessment
for serverless MapReduce on AWS Lambda. Future Generation Computer Systems 97 (2019), 259–274.
[22] Xiaodong Gu, Hongyu Zhang, and Sunghun Kim. 2018. Deep code search. In Proceedings of the International Conference
on Software Engineering. 933–944.
[23] Fatemeh Hadadi, Qinghua Xu, Domenico Bianculli, and Lionel Briand. 2024. Anomaly detection on unstable logs with
GPT models. arXiv preprint arXiv:2406.07467 (2024).
[24] Hamel Husain, Ho-Hsiang Wu, Tiferet Gazit, Miltiadis Allamanis, and Marc Brockschmidt. 2019. Codesearchnet
challenge: Evaluating the state of semantic code search. arXiv preprint arXiv:1909.09436 (2019).
[25] Abhinav Jangda, Donald Pinckney, Yuriy Brun, and Arjun Guha. 2019. Formal foundations of serverless computing.
Proceedings of the ACM on Programming Languages 3, OOPSLA (2019), 1–26.
[26] Anshul Jindal, Michael Gerndt, Mohak Chadha, Vladimir Podolskiy, and Pengfei Chen. 2021. Function delivery network:
Extending serverless computing for heterogeneous platforms. Software: Practice and Experience 51, 9 (2021), 1936–1963.
[27] Jeongchul Kim and Kyungyong Lee. 2019. Functionbench: A suite of workloads for serverless cloud function service.
In Proceedings of the IEEE International Conference on Cloud Computing. IEEE, 502–504.
, Vol. 1, No. 1, Article . Publication date: November 2025.


20
Wen et al.
[28] Kisub Kim, Dongsun Kim, Tegawendé F Bissyandé, Eunjong Choi, Li Li, Jacques Klein, and Yves Le Traon. 2018. FaCoY:
A code-to-code search engine. In Proceedings of the International Conference on Software Engineering. 946–957.
[29] Xinyu Lian, Yinfang Chen, Runxiang Cheng, Jie Huang, Parth Thakkar, and Tianyin Xu. 2023. Configuration validation
with large language models. arXiv preprint arXiv:2310.09690 (2023).
[30] Xuanzhe Liu, Jinfeng Wen, Zhenpeng Chen, Ding Li, Junkai Chen, Yi Liu, Haoyu Wang, and Xin Jin. 2023. FaaSLight:
General application-Level cold-start latency optimization for Function-as-a-Service in serverless computing. ACM
Transactions on Software Engineering and Methodology 32, 5 (2023), 1–29.
[31] Sifei Luan, Di Yang, Celeste Barnaby, Koushik Sen, and Satish Chandra. 2019. Aroma: Code recommendation via
structural code search. Proceedings of the ACM on Programming Languages 3, OOPSLA (2019), 1–28.
[32] Zexiong Ma, Shengnan An, Bing Xie, and Zeqi Lin. 2024. Compositional API recommendation for library-oriented
code generation. In Proceedings of the IEEE/ACM International Conference on Program Comprehension. 87–98.
[33] Pascal Maissen, Pascal Felber, Peter Kropf, and Valerio Schiavoni. 2020. FaaSdom: A benchmark suite for serverless
computing. In Proceedings of the ACM International Conference on Distributed and Event-based Systems. 73–84.
[34] Tam Nguyen, Phong Vu, and Tung Nguyen. 2020. Code recommendation for exception handling. In Proceedings of
the ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software
Engineering. 1027–1038.
[35] Chao Qian, Yang Yu, and Zhi-Hua Zhou. 2015. Subset selection by Pareto optimization. Advances in Neural Information
Processing Systems 28 (2015).
[36] Mukund Raghothaman, Yi Wei, and Youssef Hamadi. 2016. SWIM: synthesizing what I mean: Code search and idiomatic
snippet synthesis. In Proceedings of the International Conference on Software Engineering. 357–367.
[37] Mohammad Masudur Rahman, Chanchal K Roy, and David Lo. 2016. Rack: Automatic api recommendation using crowd-
sourced knowledge. In Proceedings of IEEE International Conference on Software Analysis, Evolution, and Reengineering,
Vol. 1. IEEE, 349–359.
[38] Saksham Sachdev, Hongyu Li, Sifei Luan, Seohyun Kim, Koushik Sen, and Satish Chandra. 2018. Retrieval on source
code: A neural code search. In Proceedings of the ACM SIGPLAN International Workshop on Machine Learning and
Programming Languages. 31–41.
[39] Mohammad Shahrad, Rodrigo Fonseca, Inigo Goiri, Gohar Chaudhry, Paul Batum, Jason Cooke, Eduardo Laureano,
Colby Tresness, Mark Russinovich, and Ricardo Bianchini. 2020. Serverless in the wild: Characterizing and optimizing
the serverless workload at a large cloud provider. In Proceedings of USENIX annual technical conference. 205–218.
[40] Vaishaal Shankar, Karl Krauth, Kailas Vodrahalli, Qifan Pu, Benjamin Recht, Ion Stoica, Jonathan Ragan-Kelley, Eric
Jonas, and Shivaram Venkataraman. 2020. Serverless linear algebra. In Proceedings of the ACM Symposium on Cloud
Computing. 281–295.
[41] Fran Silavong, Sean Moran, Antonios Georgiadis, Rohan Saphal, and Robert Otter. 2022. Senatus: A fast and accurate
code-to-code recommendation engine. In Proceedings of the International Conference on Mining Software Repositories.
511–523.
[42] Hao Wang, Di Niu, and Baochun Li. 2019. Distributed machine learning with a serverless architecture. In Proceedings
of the IEEE INFOCOM 2019-IEEE Conference on Computer Communications. IEEE, 1288–1296.
[43] Jinfeng Wen, Zhenpeng Chen, Xin Jin, and Xuanzhe Liu. 2023. Rise of the planet of serverless computing: A systematic
review. ACM Transactions on Software Engineering and Methodology 32, 5 (2023), 1–61.
[44] Jinfeng Wen, Zhenpeng Chen, Yi Liu, Yiling Lou, Yun Ma, Gang Huang, Xin Jin, and Xuanzhe Liu. 2021. An empirical
study on challenges of application development in serverless computing. In Proceedings of the ACM Joint Meeting on
European Software Engineering Conference and Symposium on the Foundations of Software Engineering. 416–428.
[45] Jinfeng Wen, Zhenpeng Chen, Jianshu Zhao, Federica Sarro, Haodi Ping, Ying Zhang, Shangguang Wang, and Xuanzhe
Liu. 2025. SCOPE: Performance testing for serverless computing. ACM Transactions on Software Engineering and
Methodology (2025).
[46] Jinfeng Wen, Yi Liu, Zhenpeng Chen, Junkai Chen, and Yun Ma. 2021. Characterizing commodity serverless computing
platforms. Journal of Software: Evolution and Process (2021), e2394.
[47] Junjielong Xu, Ruichun Yang, Yintong Huo, Chengyu Zhang, and Pinjia He. 2024. DivLog: Log parsing with prompt
enhanced in-context learning. In Proceedings of the IEEE/ACM International Conference on Software Engineering. 1–12.
[48] Xin Yin, Chao Ni, and Shaohua Wang. 2024. Multitask-based evaluation of open-source LLM on software vulnerability.
IEEE Transactions on Software Engineering (2024).
[49] Minchen Yu, Zhifeng Jiang, Hok Chun Ng, Wei Wang, Ruichuan Chen, and Bo Li. 2021. Gillis: Serving large neural
networks in serverless functions with automatic model partitioning. In Proceedings of the IEEE International Conference
on Distributed Computing Systems. IEEE, 138–148.
[50] Tianyi Yu, Qingyuan Liu, Dong Du, Yubin Xia, Binyu Zang, Ziqian Lu, Pingchao Yang, Chenggang Qin, and Haibo
Chen. 2020. Characterizing serverless platforms with serverlessbench. In Proceedings of the ACM Symposium on Cloud
Computing. 30–44.
, Vol. 1, No. 1, Article . Publication date: November 2025.


SlsReuse: LLM-Powered Serverless Function Reuse
21
[51] Zhiqiang Yuan, Mingwei Liu, Shiji Ding, Kaixin Wang, Yixuan Chen, Xin Peng, and Yiling Lou. 2024. Evaluating and
improving ChatGPT for unit test generation. Proceedings of the ACM on Software Engineering 1, FSE (2024), 1703–1726.
[52] Michael Zhang, Chandra Krintz, and Rich Wolski. 2021. Edge-adaptable serverless acceleration for machine learning
Internet of Things applications. Software: Practice and Experience 51, 9 (2021), 1852–1867.
, Vol. 1, No. 1, Article . Publication date: November 2025.
