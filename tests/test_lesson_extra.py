"""The extra lessons and missions must be correct, not just present.

Every second-prediction answer is checked by really compiling the snippet, and every
warm-up mission is solved by a reference program that must pass all of its tests.
"""
import unittest

import server
from curriculum import CURRICULUM
from lesson_extra import CHAPTERS, predict_program

# Reference solutions for the warm-up missions (never sent to the learner).
SOLUTIONS = [
    '#include <iostream>\nint main(){std::cout<<"Merhaba\\nKedi";}',
    '#include <iostream>\nint main(){int yas=3;double kilo=4.5;std::cout<<yas<<" "<<kilo;}',
    '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b;}',
    '#include <iostream>\nint main(){int s;std::cin>>s;std::cout<<s/60<<" "<<s%60;}',
    '#include <iostream>\nint main(){int t;std::cin>>t;if(t>30)std::cout<<"Sicak";else if(t<10)std::cout<<"Soguk";else std::cout<<"Ilik";}',
    '#include <iostream>\nint main(){int n;std::cin>>n;for(int i=n;i>=1;--i){std::cout<<i;if(i>1)std::cout<<" ";}}',
    '#include <iostream>\nint enBuyuk(int a,int b){return a>b?a:b;}\nint main(){int a,b;std::cin>>a>>b;std::cout<<enBuyuk(a,b);}',
    '#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int&x:v)std::cin>>x;int m=v[0];for(int x:v)if(x<m)m=x;std::cout<<m;}',
    '#include <iostream>\n#include <string>\nint main(){std::string k;std::cin>>k;std::cout<<k[0]<<k[k.size()-1];}',
    '#include <iostream>\nvoid ikiyeKatla(int& n){n*=2;}\nint main(){int a,b;std::cin>>a>>b;ikiyeKatla(a);std::cout<<a<<" "<<b;}',
    '#include <iostream>\n#include <string>\nstruct Urun{std::string ad;int fiyat;};\nint main(){Urun u;std::cin>>u.ad>>u.fiyat;u.fiyat+=u.fiyat/10;std::cout<<u.ad<<" "<<u.fiyat;}',
    '#include <iostream>\nclass Hesap{int b;public:Hesap(int x):b(x){}void yatir(int x){b+=x;}int bakiye()const{return b;}};\nint main(){int a,c;std::cin>>a>>c;Hesap h(a);h.yatir(c);std::cout<<h.bakiye();}',
    '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int&x:v)std::cin>>x;std::cout<<std::count(v.begin(),v.end(),0);}',
    '#include <iostream>\n#include <stdexcept>\nint main(){int n;std::cin>>n;try{if(n<0)throw std::runtime_error("negatif");std::cout<<n;}catch(const std::exception&e){std::cout<<"Hata: "<<e.what();}}',
    '#include <iostream>\nint main(){int n;std::cin>>n;int t=0;for(int i=0;i<n;++i){int p;std::cin>>p;t+=p;}std::cout<<t<<" "<<t/n;}',
    '#include <iostream>\nint main(){int n;std::cin>>n;int*d=new int[n];for(int i=0;i<n;++i)std::cin>>d[i];int m=d[0];for(int i=1;i<n;++i)if(d[i]>m)m=d[i];std::cout<<m;delete[] d;}',
    '#include <iostream>\n#include <memory>\nint main(){int n;std::cin>>n;auto a=std::make_unique<int>(n);*a*=3;auto b=std::move(a);std::cout<<*b;}',
    '#include <iostream>\nstruct Sekil{virtual int alan()const{return 0;}virtual ~Sekil()=default;};\nstruct Kare:Sekil{int a;Kare(int x):a(x){}int alan()const override{return a*a;}};\nint main(){int a;std::cin>>a;Kare k(a);const Sekil&s=k;std::cout<<s.alan();}',
    '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n;std::cin>>n;std::vector<int> v(n);for(int&x:v)std::cin>>x;std::cout<<std::count_if(v.begin(),v.end(),[](int x){return x%2==0;});}',
    '#include <iostream>\n#include <set>\nint main(){int n;std::cin>>n;std::set<int> s;for(int i=0;i<n;++i){int x;std::cin>>x;s.insert(x);}std::cout<<s.size();}',
]


@unittest.skipUnless(server.COMPILER, "g++ is required to verify lesson content")
class LessonExtraTests(unittest.TestCase):
    def test_second_predictions_match_real_program_output(self):
        for index, chapter in enumerate(CHAPTERS):
            with self.subTest(chapter=index + 1):
                result = server.compile_and_run(predict_program(index))
                self.assertTrue(result["ok"], result.get("error"))
                self.assertEqual(server.normalize_output(result["output"]), chapter["predict"][2])

    def test_reference_solutions_pass_every_warm_up_test_and_contain_required_tokens(self):
        self.assertEqual(len(SOLUTIONS), len(CHAPTERS))  # core chapters; c21-c24: test_modern_cpp
        for chapter, solution in zip(CURRICULUM, SOLUTIONS):
            warm = next(task for task in chapter["tasks"] if task["id"].endswith("-w1"))
            with self.subTest(task=warm["id"]):
                for term in warm["requires"]:
                    self.assertIn(term.casefold(), solution.casefold())
                for case in warm["tests"]:
                    result = server.compile_and_run(solution, case["input"])
                    self.assertTrue(result["ok"], result.get("error"))
                    self.assertEqual(server.normalize_output(result["output"]), server.normalize_output(case["expected"]))

    def test_starters_compile(self):
        for chapter in CURRICULUM:
            warm = next(task for task in chapter["tasks"] if task["id"].endswith("-w1"))
            with self.subTest(task=warm["id"]):
                self.assertTrue(server.compile_and_run(warm["starter"], warm["tests"][0]["input"])["compile_ok"])


class LessonShapeTests(unittest.TestCase):
    def test_every_chapter_has_deep_lessons_and_eight_missions_with_boss_last(self):
        for chapter in CURRICULUM:
            self.assertGreaterEqual(len(chapter["guide"]["tr"]), 5)
            self.assertEqual(len(chapter["guide"]["tr"]), len(chapter["guide"]["ru"]))
            self.assertEqual([t["kind"] for t in chapter["tasks"]], ["quiz", "predict", "quiz", "predict", "fix", "code", "code", "boss"])
            self.assertTrue(chapter["tasks"][-1]["id"].endswith("-boss"))
            for section in chapter["guide"]["tr"] + chapter["guide"]["ru"]:
                self.assertTrue(section[0].strip() and len(section[1]) > 60)

    def test_quiz_answers_are_among_the_offered_options(self):
        for chapter in CURRICULUM:
            for task in chapter["tasks"]:
                if task["kind"] != "quiz":
                    continue
                for lang in ("tr", "ru"):
                    answer = task["answer"][lang] if isinstance(task["answer"], dict) else task["answer"]
                    options = task["prompt"][lang].rsplit("(", 1)[-1].rstrip(")").split(" / ")
                    with self.subTest(task=task["id"], lang=lang):
                        self.assertIn(server.normalize_answer(answer), [server.normalize_answer(o) for o in options])


if __name__ == "__main__":
    unittest.main()
