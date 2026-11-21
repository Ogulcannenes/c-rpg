import unittest

import server
from concept_checker import check_cpp_concept
from curriculum import CURRICULUM, PREREQUISITES

SOL = {
("c16","fix"): '#include <iostream>\nint main(){int n;std::cin>>n;int* p=new int(n);*p*=2;std::cout<<*p;delete p;}',
("c16","code"): '#include <iostream>\nint main(){int n; std::cin >> n; int* a=new int[n]; int s=0; for(int i=0;i<n;i++){std::cin>>a[i]; s+=a[i];} std::cout<<s; delete[] a;}',
("c16","boss"): '#include <iostream>\nint main(){int n; std::cin >> n; int* a=new int[n]; for(int i=0;i<n;i++) std::cin>>a[i]; int* l=a; int* r=a+n-1; while(l<r){int t=*l;*l=*r;*r=t;++l;--r;} for(int i=0;i<n;i++){ if(i) std::cout<<" "; std::cout<<a[i]; } delete[] a;}',
("c17","fix"): '#include <iostream>\n#include <memory>\nint main(){int n;std::cin>>n;auto a=std::make_unique<int>(n);auto b=std::move(a);std::cout<<*b*2;}',
("c17","code"): '#include <iostream>\n#include <memory>\nint main(){int xp; std::cin >> xp; auto a=std::make_shared<int>(xp); auto b=a; *a+=10; *b+=5; std::cout<<*a<<" "<<a.use_count();}',
("c17","boss"): '#include <iostream>\nstruct Guard{ Guard(){std::cout<<"Open\\n";} ~Guard(){std::cout<<"Close\\n";} };\nint main(){int n; std::cin >> n; { Guard g; std::cout<<"Work "<<n<<"\\n"; } std::cout<<"Done";}',
("c18","fix"): '#include <iostream>\nclass Hayvan{public:virtual void ses()const{std::cout<<"...";}};\nclass Kedi:public Hayvan{public:void ses()const override{std::cout<<"Meow";}};\nint main(){Kedi k;const Hayvan& h=k;h.ses();}',
("c18","code"): '#include <iostream>\nclass Sekil{public:virtual double alan()const=0; virtual ~Sekil()=default;};\nclass Dikdortgen:public Sekil{int a,b;public:Dikdortgen(int a,int b):a(a),b(b){} double alan()const override{return a*b;}};\nclass Kare:public Sekil{int a;public:Kare(int a):a(a){} double alan()const override{return a*a;}};\nint main(){int a,b; std::cin >> a >> b; Dikdortgen d(a,b); Kare k(a); const Sekil& x=d; const Sekil& y=k; std::cout<<x.alan()<<" "<<y.alan();}',
("c18","boss"): '#include <iostream>\n#include <memory>\n#include <vector>\nclass Sekil{public:virtual long alan()const=0; virtual ~Sekil()=default;};\nclass Kare:public Sekil{long a;public:Kare(long a):a(a){} long alan()const override{return a*a;}};\nclass Dikdortgen:public Sekil{long a,b;public:Dikdortgen(long a,long b):a(a),b(b){} long alan()const override{return a*b;}};\nint main(){int n; std::cin >> n; std::vector<std::unique_ptr<Sekil>> v; for(int i=0;i<n;i++){char c; std::cin>>c; if(c==\'K\'){long a;std::cin>>a;v.push_back(std::make_unique<Kare>(a));} else {long a,b;std::cin>>a>>b;v.push_back(std::make_unique<Dikdortgen>(a,b));}} long t=0; for(auto& s: v) t+=s->alan(); std::cout<<t;}',
("c19","fix"): '#include <iostream>\nint main(){int n;std::cin>>n;int carpan=3;auto f=[carpan](int x){return x*carpan;};std::cout<<f(n);}',
("c19","code"): '#include <iostream>\ntemplate <typename T>\nT enBuyuk(T a, T b){return a>b?a:b;}\nint main(){int a,b; double c,d; std::cin >> a >> b >> c >> d; std::cout<<enBuyuk(a,b)<<" "<<enBuyuk(c,d);}',
("c19","boss"): '#include <iostream>\n#include <vector>\n#include <algorithm>\nint main(){int n; std::cin >> n; std::vector<int> v(n); for(auto& x: v) std::cin>>x; int t; std::cin>>t; std::sort(v.begin(),v.end(),[](int a,int b){return a>b;}); for(size_t i=0;i<v.size();i++){ if(i) std::cout<<" "; std::cout<<v[i]; } std::cout<<"\\n"<<std::count_if(v.begin(),v.end(),[t](int x){return x>=t;});}',
("c20","fix"): '#include <iostream>\n#include <map>\n#include <string>\nint main(){int n;std::cin>>n;std::map<std::string,int> sayac;for(int i=0;i<n;i++){std::string w;std::cin>>w;sayac[w]++;}std::cout<<sayac.size()<<" "<<sayac["cat"];}',
("c20","code"): '#include <iostream>\n#include <map>\n#include <string>\nint main(){int n; std::cin >> n; std::map<std::string,int> m; for(int i=0;i<n;i++){std::string w; std::cin>>w; m[w]++;} bool first=true; for(auto& [k,v]: m){ if(!first) std::cout<<"\\n"; first=false; std::cout<<k<<" "<<v; }}',
("c20","boss"): '#include <iostream>\n#include <set>\nint main(){int n; std::cin >> n; std::set<int> s; for(int i=0;i<n;i++){int x; std::cin>>x; s.insert(x);} std::cout<<s.size()<<"\\n"; bool f=true; for(int x: s){ if(!f) std::cout<<" "; f=false; std::cout<<x; }}',
}

NEG = {
 "pointer_dynamic": '#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2;}',
 "smart_pointer": '#include <iostream>\n#include <memory>\nint main(){int n;std::cin>>n;int* p=new int(n);std::cout<<*p*2;delete p;}',
 "raii_scope": '#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<"Open\\nWork "<<n<<"\\nClose\\nDone";}',
 "virtual_dispatch": '#include <iostream>\nint main(){std::cout<<"Meow";}',
 "template_function": '#include <iostream>\nint main(){int a,b;double c,d;std::cin>>a>>b>>c>>d;std::cout<<(a>b?a:b)<<" "<<(c>d?c:d);}',
 "lambda_capture": '#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*3;}',
 "map_set": '#include <iostream>\nint main(){std::cout<<"1\\n7";}',
}

KIND = {"fix": 4, "code": 6, "boss": 7}


@unittest.skipUnless(server.COMPILER, "C++ compiler is required")
class AdvancedChapterTests(unittest.TestCase):
    def test_new_chapters_are_wired_into_the_learning_map(self):
        self.assertEqual([c["id"] for c in CURRICULUM[15:20]], ["c16", "c17", "c18", "c19", "c20"])
        for number in range(16, 21):
            self.assertTrue(set(PREREQUISITES[number]) < set(range(1, number)) | {16, 17, 18, 19})
            chapter = CURRICULUM[number - 1]
            self.assertEqual([t["kind"] for t in chapter["tasks"]], ["quiz", "predict", "quiz", "predict", "fix", "code", "code", "boss"])
            self.assertEqual(set(chapter["title"]), {"tr", "ru"})
            self.assertEqual(len(chapter["guide"]["tr"]), len(chapter["guide"]["ru"]))

    def test_reference_solutions_pass_and_starters_fail(self):
        for chapter in CURRICULUM[15:20]:
            for kind, index in KIND.items():
                task = chapter["tasks"][index]
                with self.subTest(chapter=chapter["id"], kind=kind):
                    self.assertEqual(server.diagnose_locally(task, SOL[(chapter["id"], kind)], "", "tr")["kind"], "passed")
                    self.assertNotEqual(server.diagnose_locally(task, task["starter"], "", "tr")["kind"], "passed")

    def test_right_output_without_the_concept_is_rejected(self):
        for rule, source in NEG.items():
            with self.subTest(rule=rule):
                self.assertFalse(check_cpp_concept(source, rule, "tr")["passed"])

    def test_keywords_in_comments_and_strings_do_not_count(self):
        source = '#include <iostream>\nint main(){ // new delete int* p\n std::cout << "new delete virtual override template"; }'
        for rule in ("pointer_dynamic", "virtual_dispatch", "template_function"):
            self.assertFalse(check_cpp_concept(source, rule, "tr")["passed"])


if __name__ == "__main__":
    unittest.main()
